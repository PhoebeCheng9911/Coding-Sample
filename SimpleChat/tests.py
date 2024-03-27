import socket
import _thread
from threading import Timer
import fileinput
import codecs
import unittest
from server import Server
from client import Client
import time
import os

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)


class TestServerParsing(unittest.TestCase):
    def setUp(self):
        self.s = Server()
        self.addr = 1
        self.s.socketid_username_map[self.addr] = {"socket": None, "username": None}

    def assert_parse(self, msg, expected):
        self.assertEqual(self.s.parse_client_msg(msg, self.addr), f"> {expected}\n")

    def test_create(self):
        self.assert_parse("create", "Incorrect number of arguments. Usage: create [username] [password]")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertIn(self.addr, self.s.socketid_username_map)
        self.assertDictEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
        self.assertEqual(len(self.s.username_userinfo_map), 0)

        self.assert_parse("create user", "Incorrect number of arguments. Usage: create [username] [password]")
        self.assert_parse("create user user pwd", "Incorrect number of arguments. Usage: create [username] [password]")

        self.assert_parse("create user1 pwd1", "Created new account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertDictEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": "user1"})
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assertIn("user1", self.s.username_userinfo_map)
        self.assertDictEqual(self.s.username_userinfo_map["user1"], {"password": "pwd1", "addr": self.addr, "is_logged_in": True})

        self.assert_parse("create user2 pwd2", "Please log out before creating a new account.")
        self.assert_parse("logout", "Logged out successfully")
        self.assert_parse("create user1 pwd2", "Username is not unique, please try again.")

    def test_not_logged_in(self):
        self.assert_parse("logout", "User not logged in")
        self.assert_parse("delete", "User not logged in")
        self.assert_parse("status", "User not logged in")
        self.assert_parse("list", "User not logged in")
        self.assert_parse("list_pending", "User not logged in")

    def test_account(self):  # login, logout, status, list, delete
        self.assert_parse("create user1 pwd1", "Created new account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assert_parse("status", "user1")

        self.assert_parse("logout", "Logged out successfully")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertIn(self.addr, self.s.socketid_username_map)
        self.assertDictEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assertIn("user1", self.s.username_userinfo_map)
        self.assertDictEqual(self.s.username_userinfo_map["user1"], {"password": "pwd1", "addr": None, "is_logged_in": False})

        self.assert_parse("login user1", "Incorrect number of arguemnts. Usage: login [username] [password]")
        self.assert_parse("login user1 pwd1 pwd1", "Incorrect number of arguemnts. Usage: login [username] [password]")
        self.assert_parse("login user1 pwd2", "Failed to login, please check username and/or password and try again.")
        self.assert_parse("login user3 pwd1", "Failed to login, please check username and/or password and try again.")

        self.assert_parse("login user1 pwd1", "Successfully logged in!\n> You have 0 recent messages.\n> ")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assert_parse("status", "user1")
        self.assert_parse("login user2 pwd2", "Already logged in as user1")

        self.assert_parse("list", "Not enough info. Please enter a regular expression to match.")
        self.assert_parse("list .", "1 matches: ['user1']")
        self.assert_parse("list us*", "1 matches: ['user1']")
        self.assert_parse("list user2", "0 matches: []")

        self.assert_parse("delete", "Deleted account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertIn(self.addr, self.s.socketid_username_map)
        self.assertDictEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
        self.assertEqual(len(self.s.username_userinfo_map), 0)
        self.assert_parse("status", "User not logged in")

    def test_send_pending(self):
        self.assert_parse("create user1 pwd1", "Created new account successfully!")
        self.assert_parse("logout", "Logged out successfully")

        self.assert_parse("create user2 pwd2", "Created new account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(len(self.s.username_userinfo_map), 2)
        self.assert_parse("list_pending", "No pending messages")

        self.assert_parse("send", "Not enough info. Please enter a recipient username and message.")
        self.assert_parse("send user1", "Not enough info. Please enter a recipient username and message.")
        self.assert_parse("send user3 Hello!", "The recipient user does not exist.")
        self.assert_parse("send user1 This is a really really really really really really really really really really really really really really \
            really really really really really really really really really really really really really really really really really really really \
            really really really really really long message.", "Message is too long. Maximum message length is 280 characters.")

        self.assert_parse("send user1 Hello! Once upon a time...", "Sent message to user1 successfully, they will see it when they log back on!")
        self.assertEqual(len(self.s.pending_messages), 1)
        self.assert_parse("list_pending", "['user1: Hello! Once upon a time...']")

        self.assert_parse("send user1 The End.", "Sent message to user1 successfully, they will see it when they log back on!")
        self.assertEqual(len(self.s.pending_messages), 2)
        self.assert_parse("list_pending", "['user1: Hello! Once upon a time...', 'user1: The End.']")

        self.assert_parse("logout", "Logged out successfully")

        self.assert_parse("login user1 pwd1", "Successfully logged in!\n> You have 2 recent messages.\n> user2: Hello! Once upon a time...\n> user2: The End.")
        self.assertEqual(len(self.s.pending_messages), 0)

    def test_delete_pending(self):
        self.assert_parse("create user1 pwd1", "Created new account successfully!")
        self.assert_parse("logout", "Logged out successfully")

        self.assert_parse("create user2 pwd2", "Created new account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(len(self.s.username_userinfo_map), 2)
        self.assert_parse("list_pending", "No pending messages")

        self.assert_parse("send user1 Hello! Once upon a time...", "Sent message to user1 successfully, they will see it when they log back on!")
        self.assertEqual(len(self.s.pending_messages), 1)
        self.assert_parse("list_pending", "['user1: Hello! Once upon a time...']")

        self.assert_parse("delete", "Deleted account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assertEqual(len(self.s.pending_messages), 0)
        self.assert_parse("status", "User not logged in")

        self.assert_parse("login user1 pwd1", "Successfully logged in!\n> You have 0 recent messages.\n> ")


class TestSend(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        _thread.start_new_thread(self.server.start_server, tuple())
        time.sleep(2)  # wait for server to start
        self.client1 = Client('tests/client1.out')
        self.client2 = Client('tests/client2.out')
        time.sleep(2)  # wait for clients to connect
        self.assertEqual(len(self.server.socketid_username_map), 2)

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
        self.client1.sendline("create user1 pwd\n")
        self.client2.sendline("create user2 pwd\n")
        time.sleep(2)
        self.assertEqual(len(self.server.username_userinfo_map), 2)
        self.assertIn("user1", self.server.username_userinfo_map)
        self.assertIn("user2", self.server.username_userinfo_map)

        self.client1.sendline("send user2 hello there!\n")
        time.sleep(2)
        self.client2.sendline("send user1 hello to you too!\n")
        time.sleep(2)
        self.client2.sendline("logout\n")
        time.sleep(2)

        # test messages larger than buffer size (1024b)
        for i in range(5):
            # send 280 a's
            self.client1.sendline(
                "send user2 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n")
        time.sleep(2)
        self.assertEqual(len(self.server.pending_messages), 5)
        self.client1.sendline("list_pending\n")
        self.client2.sendline("login user2 pwd\n")
        time.sleep(2)

        self.compare_files('tests/client1.out', 'tests/client1.exp')
        self.compare_files('tests/client2.out', 'tests/client2.exp')


if __name__ == "__main__":
    unittest.main()
