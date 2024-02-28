import socket
import _thread
from threading import Timer
import re
import time
import codecs
import os
import json
from threading import Thread
import sys

'''
Command line workflow
fuser -k 65433/tcp # kill the server to restart it
python3 server.py
python3 client.py
'''

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)


def get_username_password(msg):
    return tuple(msg.split(" ")[1:3])


def get_first_arg(msg):
    return msg.split(" ")[1]


def get_num_args(msg):
    return len(msg.split(" "))-1


class Server:
    def __init__(self, is_test=False):
        if is_test:
            self.pending_messages_path = "tests/pending_messages.json"
            self.userinfo_path = "tests/userinfo.json"
        else:
            self.pending_messages_path = "data/pending_messages.json"
            self.userinfo_path = "data/userinfo.json"
        self.pending_messages = []  # [{sender,receiver,timestamp,message},...]
        self.socketid_username_map = {}  # key=addr, val={socket,username}
        self.username_userinfo_map = {}  # key=username, val={addr,password,is_logged_in}
        self.init_state()

    def init_state(self):
        if os.path.exists(self.pending_messages_path):
            with open(self.pending_messages_path, 'r') as f:
                self.pending_messages = json.load(f)
        if os.path.exists(self.userinfo_path):
            with open(self.userinfo_path, 'r') as f:
                self.username_userinfo_map = json.load(f)
            for k in self.username_userinfo_map.keys():
                self.username_userinfo_map[k]["addr"] = None
                self.username_userinfo_map[k]["is_logged_in"] = False

    def update_userinfo(self):
        with open(self.userinfo_path, "w") as final:
            # save the current usernames and passwords
            userinfo = {k: {'password': v['password']} for k, v in self.username_userinfo_map.items()}
            json.dump(userinfo, final)

    def update_pending_messages(self):
        with open(self.pending_messages_path, "w") as final:
            json.dump(self.pending_messages, final)

    def start_server(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen()
            print(f"Connected to {host}::{port}")
            while True:
                if len(self.socketid_username_map) < 50:  # max 50 clients connected at once
                    # For each new connected client, create a new thread
                    conn, addr = s.accept()
                    _thread.start_new_thread(self.on_new_client, (conn, addr))

    def on_new_client(self, clientsocket, addr):
        self.socketid_username_map[addr] = {"socket": clientsocket, "username": None}
        msgs = ''
        while True:
            new_msgs = clientsocket.recv(1024)
            if not new_msgs:
                break
            msgs += codecs.decode(new_msgs)  # concatenate new messages to unfinished messages (if any)
            msgs = msgs.split('\n')  # separate commands
            finished_msg = True
            for msg in msgs:
                if msg == '':  # last char is '\n'
                    continue
                if int(msg[:3]) == len(msg[3:]):  # check if message length is correct (if we've received the entire message)
                    msg = msg[3:]
                    return_msg = bytes(self.parse_client_msg(msg, addr), 'utf-8')
                    clientsocket.send(return_msg)
                else:  # unfinished message
                    finished_msg = False
                    msgs = msg
            if finished_msg:
                msgs = ''
        clientsocket.close()

    def parse_client_msg(self, msg, addr):
        msg_type = msg.split(" ")[0]

        if msg_type == "create":
            if get_num_args(msg) != 2:
                return "> Incorrect number of arguments. Usage: create [username] [password]\n"
            if self.socketid_username_map[addr]["username"]:
                return "> Please log out before creating a new account.\n"
            username, password = get_username_password(msg)
            if not (username.isalnum() and password.isalnum() and len(username) <= 24 and len(password) <= 24):
                return "> Invalid username and/or password. Username and password must be at most 24 alphanumeric characters.\n"
            if username not in self.username_userinfo_map:
                # register new client
                self.socketid_username_map[addr]["username"] = username
                self.username_userinfo_map[username] = {"addr": addr, "password": password, "is_logged_in": True}
                self.update_userinfo()
                return "> Created new account successfully!\n"
            else:
                # username is not unique, return error
                return "> Username is not unique, please try again.\n"

        if msg_type == "login":
            if get_num_args(msg) != 2:
                return "> Incorrect number of arguemnts. Usage: login [username] [password]\n"
            if self.socketid_username_map[addr]['username']:
                return f"> Already logged in as {self.socketid_username_map[addr]['username']}\n"
            username, password = get_username_password(msg)
            if username in self.username_userinfo_map and self.username_userinfo_map[username]["password"] == password:
                if self.username_userinfo_map[username]['is_logged_in']:  # users are not allowed to be logged in on multiple clients
                    return f"> Failed to login, this account is already logged in on a different client.\n"
                # log user in
                # update user metadata
                self.socketid_username_map[addr]["username"] = username
                self.username_userinfo_map[username]["is_logged_in"] = True
                # return all pending messages for this user
                user_messages = [f"{msg['sender']}: {msg['message']}" for msg in self.pending_messages if msg["receiver"] == username]
                n_messages = len(user_messages)
                user_messages = "\n> ".join(user_messages)
                # delete all newly delivered messages
                self.pending_messages = [msg for msg in self.pending_messages if msg["receiver"] != username]
                self.update_pending_messages()
                return f"> Successfully logged in!\n> You have {n_messages} recent messages.\n> {user_messages}\n"  # TODO: edge case: length of user_messages may be too long
            else:
                # failed to login, return error
                return "> Failed to login, please check username and/or password and try again.\n"
            pass

        # remaining comands (logout, delete, status, list, send, list_pending) all require user to be logged in
        if not self.socketid_username_map[addr]["username"]:
            return "> User not logged in\n"

        if msg_type == "logout":
            username = self.socketid_username_map[addr]["username"]
            self.username_userinfo_map[username]["is_logged_in"] = False
            self.username_userinfo_map[username]["addr"] = None
            self.socketid_username_map[addr]["username"] = None
            return "> Logged out successfully\n"

        if msg_type == "delete":
            # delete account from server metadata
            username = self.socketid_username_map[addr]["username"]
            self.username_userinfo_map.pop(username)
            self.update_userinfo()
            # remove messages from/to this user
            self.pending_messages = [msg for msg in self.pending_messages if msg["sender"] != username and msg["receiver"] != username]
            self.update_pending_messages()
            self.socketid_username_map[addr]["username"] = None
            return "> Deleted account successfully!\n"

        if msg_type == "status":
            # Return username if the client is logged in
            return f'> {self.socketid_username_map[addr]["username"]}\n'

        if msg_type == "list":
            if get_num_args(msg) < 1:
                return "> Not enough info. Please enter a regular expression to match.\n"
            wildcard = get_first_arg(msg)
            # Return all usernames matchine wildcard
            matches = [usr for usr in self.username_userinfo_map.keys() if re.search(wildcard, usr) is not None]
            return f"> {len(matches)} matches: {str(matches)}\n"

        if msg_type == "send":
            if get_num_args(msg) < 2:
                return "> Not enough info. Please enter a recipient username and message.\n"
            recipient_username = get_first_arg(msg)
            message = " ".join(msg.split(" ")[2:])
            if len(message) > 280:
                return "> Message is too long. Maximum message length is 280 characters.\n"
            if recipient_username not in self.username_userinfo_map:  # NOTE(janet): will there be an error if the recipient is the same as the sender?
                return "> The recipient user does not exist.\n"
            username = self.socketid_username_map[addr]["username"]
            if self.username_userinfo_map[recipient_username]["is_logged_in"]:
                # send message to recipient right now, if they are currently logged in
                recipient_addr = self.username_userinfo_map[recipient_username]["addr"]
                self.socketid_username_map[recipient_addr]["socket"].send(bytes(f"> {username}: {message}\n", 'utf-8'))
                return f"> Sent message to {recipient_username} successfully!\n"
            else:
                # send message to recipient once they arrive online
                self.pending_messages.append({"sender": username, "receiver": recipient_username, "timestamp": time.time(), "message": message})
                self.update_pending_messages()
                return f"> Sent message to {recipient_username} successfully, they will see it when they log back on!\n"

        if msg_type == "list_pending":
            username = self.socketid_username_map[addr]["username"]
            users_messages = [msg for msg in self.pending_messages if msg["sender"] == username]
            if len(users_messages) == 0:
                return "> No pending messages\n"
            messages = str([f'{msg["receiver"]}: {msg["message"]}' for msg in users_messages])
            return f"> {messages}\n"
        return "> Unknown message type, please try again\n"


def get_conn_info():
    host, port = HOST, PORT
    if (len(sys.argv) == 3):
        try:
            host = sys.argv[1]
            port = int(sys.argv[2])
        except ValueError:
            sys.exit("Usage: \n python3 server.py \n or \n python3 server.py [string: host1] [int: port1]")
    return host, port


if __name__ == "__main__":
    server = Server()
    host, port = get_conn_info()
    server.start_server(host, port)
