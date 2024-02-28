import socket
import _thread
from threading import Timer
import fileinput
import codecs
import unittest
from server import serve
from client import Client
import time
import os

import grpc
import gRPC_pb2
import gRPC_pb2_grpc
from concurrent import futures


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)


class TestSingleClient(unittest.TestCase):
    def setUp(self):
        _thread.start_new_thread(serve, tuple())
        time.sleep(2)
        self.c = Client('tests/client.out')

    def tearDown(self):
        os.remove('tests/client.out')

    def compare_files(self, file1, file2):
        with open(file1, 'r') as f1:
            lines1 = f1.readlines()
        with open(file2, 'r') as f2:
            lines2 = f2.readlines()
        self.assertListEqual(lines1, lines2)

    def test_single_client(self):
        # create, logout
        self.c.sendline("create user")  # incorrect number of args
        self.c.sendline("create user1 pwd1")
        time.sleep(2)
        self.c.sendline("create user2 pwd2")  # logout before creating new account
        self.c.sendline("logout")
        self.c.sendline("create user1 pwd2")  # username not unique

        # user is not logged in
        self.c.sendline("delete")
        self.c.sendline("status")
        self.c.sendline("list .")
        self.c.sendline("list_pending")

        # login, status, list
        self.c.sendline("login user1")  # incorrect number of args
        self.c.sendline("login user1 pwd2")  # incorrect password
        self.c.sendline("login user1 pwd1")
        time.sleep(2)
        self.c.sendline("status")  # user1
        self.c.sendline("login user2 pwd1")  # already logged in

        # # delete
        self.c.sendline("delete")
        time.sleep(2)
        self.c.sendline("status")  # not logged in

        # send (pending)
        self.c.sendline("create user1 pwd1")
        time.sleep(2)
        self.c.sendline("logout")
        self.c.sendline("create user2 pwd2")
        time.sleep(2)
        self.c.sendline("send user1")  # incorrect number of args
        self.c.sendline("send user3 Hello!")  # recipient does not exist
        self.c.sendline("send user1 This is a really really really really really really really really really really really really really really \
            really really really really really really really really really really really really really really really really really really really \
            really really really really really long message.")  # message too long
        self.c.sendline("list_pending")  # no response
        self.c.sendline("send user1 Hello! Once upon a time...")
        self.c.sendline("list_pending")  # [('user2', 'Hello! Once upon a time...')]
        self.c.sendline("logout")
        self.c.sendline("login user1 pwd1")  # 1 recent message. [user2] Hello! Once upon a time...
        time.sleep(2)

        # # delete while user has pending messages
        self.c.sendline("send user2 Hello! Once upon a time...")
        self.c.sendline("list_pending")
        self.c.sendline("delete")
        self.c.sendline("status")
        self.c.sendline("login user2 pwd2")  # 0 recent messages
        time.sleep(2)
        self.c.sendline("list .")

        self.compare_files('tests/client.out', 'tests/client.exp')


class TestSend(unittest.TestCase):
    def setUp(self):
        _thread.start_new_thread(serve, tuple())
        time.sleep(2)
        self.client1 = Client('tests/client1.out')
        self.client2 = Client('tests/client2.out')

    def tearDown(self):
        os.remove('tests/client1.out')
        os.remove('tests/client2.out')

    def compare_files(self, file1, file2):
        with open(file1, 'r') as f1:
            lines1 = f1.readlines()
        with open(file2, 'r') as f2:
            lines2 = f2.readlines()
        self.assertListEqual(lines1, lines2)

    def test_send(self):
        self.client1.sendline("create user1 pwd")
        self.client2.sendline("create user2 pwd")
        time.sleep(2)

        self.client1.sendline("send user2 hello there!")
        time.sleep(2)
        self.client2.sendline("send user1 hello to you too!")
        time.sleep(2)
        self.client2.sendline("logout")
        time.sleep(2)
        self.client1.sendline("send user2 are you there?")
        time.sleep(2)
        self.client2.sendline("login user2 pwd")
        time.sleep(2)
        self.client1.sendline("delete")
        self.client2.sendline("delete")
        time.sleep(2)

        self.compare_files('tests/client1.out', 'tests/client1.exp')
        self.compare_files('tests/client2.out', 'tests/client2.exp')


if __name__ == "__main__":
    unittest.main()
