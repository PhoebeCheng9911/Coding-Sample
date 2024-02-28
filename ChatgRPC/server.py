from concurrent import futures
import math
import time

import grpc
import gRPC_pb2
import gRPC_pb2_grpc

import socket
import _thread
import re
import time
import codecs
from reportlab.pdfgen import canvas

# Reference: https://grpc.io/docs/languages/python/basics/

pending_messages = []  # [{sender,receiver,timestamp,message},...]
socketid_username_map = {}  # key=addr, val={socket,username}
username_userinfo_map = {}  # key=username, val={addr,password,is_logged_in}
# Each message is of type gRPC_pb2.ChatMessage()


class ChatServerServicer(gRPC_pb2_grpc.ChatServerServicer):
    """Provides methods that implement functionality of route guide server."""

    def __init__(self):
        self.chats = []
        pass

    def Login(self, request, context):
        global pending_messages
        if not (request.username.isalnum() and request.password.isalnum() and len(request.username) <= 24 and len(request.password) <= 24):
            return gRPC_pb2.ReturnStatusPayload(success=False, serverMsg="Invalid username and/or password. Username and password must be at most 24 alphanumeric characters.")
        if request.username in username_userinfo_map and username_userinfo_map[request.username]["password"] == request.password:
            if username_userinfo_map[request.username]["is_logged_in"]:
                return gRPC_pb2.ReturnStatusPayload(success=False, serverMsg="Failed to login, this account is already logged in on a different client.")
            # log user in
            # update user metadata
            username_userinfo_map[request.username]["is_logged_in"] = True  # NOTE(janet): we might want to check that user is not alrdy logged in (could be logged in on diff socket addr)
            # return all pending messages for this user
            user_messages = [match for match in pending_messages if match["receiver"] == request.username]
            n_messages = len(user_messages)
            user_messages = [gRPC_pb2.ChatMessage(receiver_username=match["receiver"], sender_username=match["sender"], message=match["message"]) for match in user_messages]
            # delete all newly delivered messages
            pending_messages = [msg for msg in pending_messages if msg["receiver"] != request.username]
            return gRPC_pb2.ReturnStatusPayload(success=True, successPayload=gRPC_pb2.PendingMessagesPayload(msg=user_messages))
        else:
            # failed to login, return error
            return gRPC_pb2.ReturnStatusPayload(success=False, serverMsg="Failed to login, please check username and/or password and try again.")

    def CreateAct(self, request, context):
        if request.username not in username_userinfo_map:
            # register new client
            username_userinfo_map[request.username] = {"password": request.password, "is_logged_in": True}
            return gRPC_pb2.SuccessStatus(success=True)
        else:
            # username is not unique, return error
            return gRPC_pb2.SuccessStatus(success=False)

    def DeleteAct(self, request, context):
        global pending_messages 
        username_userinfo_map.pop(request.username)
        # remove messages from/to this user
        pending_messages = [msg for msg in pending_messages if msg["sender"] != request.username and msg["receiver"] != request.username]
        return gRPC_pb2.SuccessStatus(success=True)

    def ListUsernames(self, request, context):
        matches = [usr for usr in username_userinfo_map.keys() if re.search(request.wildcard, usr) is not None]
        return gRPC_pb2.Usernames(usernames=[gRPC_pb2.Username(username=usr) for usr in matches])
    def SendMsg(self, request, context):
        if len(request.msg) > 280:
            return gRPC_pb2.ReturnStatusPayload(success=False, serverMsg="Message is too long. Maximum message length is 280 characters.")
            return "Message is too long. Maximum message length is 280 characters."
        if request.receiver_username not in username_userinfo_map:
            return gRPC_pb2.ReturnStatusPayload(success=False, serverMsg="The recipient user does not exist.")
        if username_userinfo_map[request.receiver_username]["is_logged_in"]:
            # send message to recipient right now, if they are currently logged in
            #recipient_addr = self.username_userinfo_map[request.receiver_username]["addr"]
            #self.socketid_username_map[recipient_addr]["socket"].send(bytes(f"{request.username}: {request.message}", 'utf-8'))
            self.SendChatMessageInternal(request, context)
            return gRPC_pb2.ReturnStatusPayload(success=True, serverMsg=f"")
        else:
            # send message to recipient once they arrive online
            pending_messages.append({"sender": request.sender_username, "receiver": request.receiver_username, "timestamp": time.time(), "message": request.msg})
            return gRPC_pb2.ReturnStatusPayload(success=True, serverMsg=f"Sent message to {request.receiver_username} successfully, they will see it when they log back on!")
        pass

    def ListPendingMsgs(self, request, context):
        users_messages = [msg for msg in pending_messages if msg["sender"] == request.username]
        return gRPC_pb2.PendingMessagesPayload(msg=[gRPC_pb2.ChatMessage(receiver_username=match["receiver"], sender_username=match["sender"], message=match["message"]) for match in users_messages])

    def Logout(self, request, context):
        if request.username in username_userinfo_map:
            username_userinfo_map[request.username]["is_logged_in"] = False
            return gRPC_pb2.SuccessStatus(success=True)
        else:
            print(f"Error: couldn't find user {request.username} to mark them as logged out")
            return gRPC_pb2.SuccessStatus(success=False)

    def ChatStream(self, request_iterator, context):
        lastindex = 0
        # Start infinite loop
        while True:
            # Check if there are any new messages
            while len(self.chats) > lastindex:
                n = self.chats[lastindex]
                lastindex += 1
                yield n

    def SendChatMessageInternal(self, request, context):
        # Add it to the chat history
        self.chats.append(request)
        return gRPC_pb2.Empty()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gRPC_pb2_grpc.add_ChatServerServicer_to_server(
        ChatServerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
