import unittest
from server import Server
from client import Client
import time
import os
import shutil
import json

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)
N_SERVERS = 3


class TestServerParsing(unittest.TestCase):
    def setUp(self):
        self.s = Server(is_test=True)
        self.addr = 1
        self.s.socketid_username_map[self.addr] = {"socket": None, "username": None}

    def tearDown(self):
        if os.path.exists(self.s.pending_messages_path):
            os.remove(self.s.pending_messages_path)
        if os.path.exists(self.s.userinfo_path):
            os.remove(self.s.userinfo_path)

    def assert_parse(self, msg, expected):
        self.assertEqual(self.s.parse_client_msg(msg, self.addr), f"> {expected}\n")

    def test_create(self):
        self.assert_parse("create", "Incorrect number of arguments. Usage: create [username] [password]")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertIn(self.addr, self.s.socketid_username_map)
        self.assertEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
        self.assertEqual(len(self.s.username_userinfo_map), 0)

        self.assert_parse("create user", "Incorrect number of arguments. Usage: create [username] [password]")
        self.assert_parse("create user user pwd", "Incorrect number of arguments. Usage: create [username] [password]")

        self.assert_parse("create user1 pwd1", "Created new account successfully!")
        self.assertEqual(len(self.s.socketid_username_map), 1)
        self.assertEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": "user1"})
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assertIn("user1", self.s.username_userinfo_map)
        self.assertEqual(self.s.username_userinfo_map["user1"], {"password": "pwd1", "addr": self.addr, "is_logged_in": True})

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
        self.assertEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
        self.assertEqual(len(self.s.username_userinfo_map), 1)
        self.assertIn("user1", self.s.username_userinfo_map)
        self.assertEqual(self.s.username_userinfo_map["user1"], {"password": "pwd1", "addr": None, "is_logged_in": False})

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
        self.assertEqual(self.s.socketid_username_map[self.addr], {"socket": None, "username": None})
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


class TestPersist(unittest.TestCase):
    def setUp(self):
        shutil.copy("tests/init_pending_messages.json", "tests/pending_messages.json")
        shutil.copy("tests/init_userinfo.json", "tests/userinfo.json")
        self.s = Server(is_test=True)
        self.addr = 1
        self.s.socketid_username_map[self.addr] = {"socket": None, "username": None}

    def tearDown(self):
        if os.path.exists(self.s.pending_messages_path):
            os.remove(self.s.pending_messages_path)
        if os.path.exists(self.s.userinfo_path):
            os.remove(self.s.userinfo_path)

    def assert_parse(self, msg, expected):
        self.assertEqual(self.s.parse_client_msg(msg, self.addr), f"> {expected}\n")

    def test_init_state(self):
        self.assertEqual(len(self.s.username_userinfo_map), 2)
        self.assert_parse("create user1 pwd2", "Username is not unique, please try again.")
        self.assert_parse("create user2 pwd1", "Username is not unique, please try again.")

        self.assertEqual(len(self.s.pending_messages), 3)
        self.assert_parse("login user1 pwd1", "Successfully logged in!\n> You have 1 recent messages.\n> user2: Hi!")
        self.assertEqual(len(self.s.pending_messages), 2)
        self.assert_parse("logout", "Logged out successfully")
        self.assert_parse("login user2 pwd2", "Successfully logged in!\n> You have 2 recent messages.\n> user1: Hello!\n> user1: Hey!")
        self.assertEqual(len(self.s.pending_messages), 0)

    def test_update_userinfo(self):
        self.assert_parse("create user3 pwd3", "Created new account successfully!")
        self.assertEqual(len(self.s.username_userinfo_map), 3)
        with open(self.s.userinfo_path, "r") as f:
            userinfo = json.load(f)
        with open("tests/exp_userinfo.json", "r") as f:
            exp_userinfo = json.load(f)
        self.assertEqual(userinfo, exp_userinfo)

    def test_update_pending_messages(self):
        self.assert_parse("login user1 pwd1", "Successfully logged in!\n> You have 1 recent messages.\n> user2: Hi!")
        self.assertEqual(len(self.s.pending_messages), 2)
        with open(self.s.pending_messages_path, "r") as f:
            pending_messages = json.load(f)
        with open("tests/exp_pending_messages1.json", "r") as f:
            exp_pending_messages = json.load(f)
        self.assertEqual(pending_messages, exp_pending_messages)

        self.assert_parse("send user2 Howdy!", "Sent message to user2 successfully, they will see it when they log back on!")
        self.assertEqual(len(self.s.pending_messages), 3)
        with open(self.s.pending_messages_path, "r") as f:
            pending_messages = json.load(f)
        with open("tests/exp_pending_messages2.json", "r") as f:
            exp_pending_messages = json.load(f)
        exp_pending_messages[2]["timestamp"] = pending_messages[2]["timestamp"]  # ignore expected timestamp for new pending message
        self.assertEqual(pending_messages, exp_pending_messages)


if __name__ == "__main__":
    unittest.main()
