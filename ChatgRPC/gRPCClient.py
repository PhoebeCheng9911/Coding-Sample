from __future__ import print_function

import logging
import random
import threading

import grpc
import gRPC_pb2
import gRPC_pb2_grpc
import fileinput

username = None

def __listen_for_messages(stub):
        # This method runs in a different thread to continually listen for messages
        try:
            for note in stub.ChatStream(gRPC_pb2.Empty()):
                if note.receiver_username == username:
                    # NOTE: this is a security/performance flaw, since each client is sent ALL messages
                    print("[{}] {}".format(note.sender_username, note.message))
        except:
            print("server disconnected")

def guide_login(stub,usrname,password):
    global username
    if username is not None:
        return f"Already logged in as {username}"
    response = stub.Login(gRPC_pb2.AuthenticationToken(username=usrname,password=password))
    if response.success:
        username = usrname
        messages = response.successPayload.msg
        messages = "\n".join(f"[{msg.sender_username}] {msg.message}" for msg in messages)
        return f"Welcome back!\nYou have {len(response.successPayload.msg)} recent message(s).\n{messages}"
    else:
        return response.serverMsg
                
def guide_create_acct(stub,usrname,password):
    global username
    response = stub.CreateAct(gRPC_pb2.AuthenticationToken(username=usrname,password=password))
    if response.success:
        username = usrname
        return "Created new account successfully!"
    else:
        # username is not unique, return error
        return "Username is not unique, please try again."

def guide_logout(stub):
    global username
    response = stub.Logout(gRPC_pb2.Username(username=username))
    if response.success:
        username = None
        assert(username is None)
        return "Logged out successfully"
    else:
        return "Failed to logout"
def guide_delete_acct(stub):
    response = stub.DeleteAct(gRPC_pb2.Username(username=username))
    if response.success:
        return "Delete account successfully, logging out"
    else:
        return "Failed to delete account, please try again"
def guide_status(stub):
    global username
    if username is not None:
        return username
    else:
        return "Not logged in"
def guide_list_usernames(stub,wildcard):
    response = stub.ListUsernames(gRPC_pb2.ListUsernamesParams(wildcard=wildcard))
    return response.usernames

def guide_list_pending_messages(stub):
    response = stub.ListPendingMsgs(gRPC_pb2.Username(username=username))
    msgs = response.msg
    return [(m.sender_username,m.message) for m in msgs]

def guide_send_msg(stub,sender_username, receiver_username,msg):
    response = stub.SendMsg(gRPC_pb2.SendParams(receiver_username=receiver_username,sender_username=sender_username,msg=msg))
    if response.success:
        return response.serverMsg
    else:
        return response.serverMsg

def get_username_password(msg):
    return tuple(msg.split(" ")[1:3])
def get_first_arg(msg):
    return msg.split(" ")[1]
def get_num_args(msg):
    return len(msg.split(" "))-1

def parse_client_msg(stub,msg):
    global username
    msg_type = msg.split(" ")[0]
    if msg_type == "create":
            if get_num_args(msg)<2:
                return "Not enough arguments. Please enter a username and a password."
            usrname,password = get_username_password(msg)
            return guide_create_acct(stub,usrname,password)
    
    if msg_type == "login":
            if get_num_args(msg)<2:
                return "Not enough arguments. Please enter a username and a password."
            usrname,password = get_username_password(msg)
            return guide_login(stub,usrname,password)
    
    if msg_type == "logout":
            return guide_logout(stub)

    if msg_type == "delete":
            return guide_delete_acct(stub)

    if msg_type == "status":
        return guide_status(stub)

    if msg_type == "list":
        return guide_list_pending_messages(stub)

    if msg_type == "send":
        if get_num_args(msg)<1:
            return "Not enough info. Please enter a recipient username and message."
        recipient_username = get_first_arg(msg)
        message = " ".join(msg.split(" ")[2:])
        return guide_send_msg(stub,username, recipient_username,message)

    if msg_type == "list_pending":
        return guide_list_pending_messages(stub)
    if not msg_type:
        return
    return "Unknown message type, please try again"
    pass

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    global username
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = gRPC_pb2_grpc.ChatServerStub(channel)
        # create new listening thread for when new message streams come in
        threading.Thread(target=lambda: __listen_for_messages(stub), daemon=True).start()
        for line in fileinput.input():
            line=line.rstrip('\n') # strip trailing newline
            response = parse_client_msg(stub,line)
            if response:
                print(response)
            #else:
            #    break


if __name__ == '__main__':
    run()