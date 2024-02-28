from __future__ import print_function

import logging
import random
import threading

import grpc
import gRPC_pb2
import gRPC_pb2_grpc
import fileinput


def get_username_password(msg):
    return tuple(msg.split(" ")[1:3])


def get_first_arg(msg):
    return msg.split(" ")[1]


def get_num_args(msg):
    return len(msg.split(" "))-1


class Client():
    def __init__(self, out_file=None):
        self.out_file = out_file  # if not None, write output to file
        self.username = None
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = gRPC_pb2_grpc.ChatServerStub(channel)
        # create new listening thread for when new message streams come in
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def run(self):
        for line in fileinput.input():
            line = line.rstrip('\n')  # strip trailing newline
            self.sendline(line)

    def sendline(self, line):
        response = self.parse_client_msg(line)
        if response:
            if self.out_file:
                with open(self.out_file, 'a') as f:
                    f.write(str(response)+'\n')
            else:
                print(response)

    def listen_for_messages(self):
        try:
            # This method runs in a different thread to continually listen for messages
            for note in self.stub.ChatStream(gRPC_pb2.Empty()):
                if note.receiver_username == self.username:
                    # NOTE: this is a security/performance flaw, since each client is sent ALL messages
                    message = "[{}] {}".format(note.sender_username, note.message)
                    if self.out_file:
                        with open(self.out_file, 'a') as f:
                            f.write(message+"\n")
                    else:
                        print(message)
        except:
            "Server disconnected"

    def guide_login(self, usrname, password):
        if self.username is not None:
            return f"Already logged in as {self.username}"
        response = self.stub.Login(gRPC_pb2.AuthenticationToken(username=usrname, password=password))
        if response.success:
            self.username = usrname
            messages = response.successPayload.msg
            messages = "\n".join(f"[{msg.sender_username}] {msg.message}" for msg in messages)
            return f"Welcome back!\nYou have {len(response.successPayload.msg)} recent message(s).\n{messages}"
        else:
            return response.serverMsg

    def guide_create_acct(self, usrname, password):
        if self.username:
            return "Please log out before creating a new account."
        response = self.stub.CreateAct(gRPC_pb2.AuthenticationToken(username=usrname, password=password))
        if response.success:
            self.username = usrname
            return "Created new account successfully!"
        else:
            return "Username is not unique, please try again."

    def guide_logout(self):
        if not self.username:
            return "Not logged in"
        response = self.stub.Logout(gRPC_pb2.Username(username=self.username))
        if response.success:
            self.username = None
            return "Logged out successfully"
        else:
            return "Failed to logout"

    def guide_delete_acct(self):
        if not self.username:
            return "Not logged in"
        response = self.stub.DeleteAct(gRPC_pb2.Username(username=self.username))
        if response.success:
            self.username = None
            return "Delete account successfully, logging out"
        else:
            return "Failed to delete account, please try again"

    def guide_status(self):
        if self.username:
            return self.username
        else:
            return "Not logged in"

    def guide_list_usernames(self, wildcard):
        if not self.username:
            return "Not logged in"
        response = self.stub.ListUsernames(gRPC_pb2.ListUsernamesParams(wildcard=wildcard))
        return response.usernames

    def guide_list_pending_messages(self):
        if not self.username:
            return "Not logged in"
        response = self.stub.ListPendingMsgs(gRPC_pb2.Username(username=self.username))
        msgs = response.msg
        return [(m.sender_username, m.message) for m in msgs]

    def guide_send_msg(self, sender_username, receiver_username, msg):
        if not self.username:
            return "Not logged in"
        response = self.stub.SendMsg(gRPC_pb2.SendParams(receiver_username=receiver_username, sender_username=sender_username, msg=msg))
        if response.success:
            return response.serverMsg
        else:
            return response.serverMsg

    def parse_client_msg(self, msg):
        msg_type = msg.split(" ")[0]
        if msg_type == "create":
            if get_num_args(msg) < 2:
                return "Not enough arguments. Please enter a username and a password."
            usrname, password = get_username_password(msg)
            return self.guide_create_acct(usrname, password)

        if msg_type == "login":
            if get_num_args(msg) < 2:
                return "Not enough arguments. Please enter a username and a password."
            usrname, password = get_username_password(msg)
            return self.guide_login(usrname, password)

        if msg_type == "logout":
            return self.guide_logout()

        if msg_type == "delete":
            return self.guide_delete_acct()

        if msg_type == "status":
            return self.guide_status()

        if msg_type == "list":
            if get_num_args(msg) < 1:
                return "Not enough arguments. Please enter a wildcard (regex)."
            wildcard = get_first_arg(msg)
            return self.guide_list_usernames(wildcard)

        if msg_type == "send":
            if get_num_args(msg) < 2:
                return "Not enough info. Please enter a recipient username and message."
            recipient_username = get_first_arg(msg)
            message = " ".join(msg.split(" ")[2:])
            return self.guide_send_msg(self.username, recipient_username, message)

        if msg_type == "list_pending":
            return self.guide_list_pending_messages()

        return "Unknown message type, please try again"


if __name__ == '__main__':
    c = Client()
    c.run()
