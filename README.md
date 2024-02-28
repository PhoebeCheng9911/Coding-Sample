# cs262-wire-protocols


### User instructions
Use one terminal for the server, and one additional terminal for each connected client.
To start the server
```
python3 server.py
```
To start a client
```
python3 client.py
```
### Client terminal instructions
Input client actions on the command line.
Clients can send messages to one another, as well as performing a variety of login/logout/status functions, by typing messages on the command line after running ``python3 client.py`` to startup the client and connect to the server.

Below, we list commands a user can send on the command line along with the parameters for those commands. Before doing anything,
a client must either create a new account or login to an existing account. To switch accounts, you must logout before logging back in. To list all usernames matching a specific text wildcard, input the command "list <regex>". To see your current account, input "status", which will return your current username if you are logged in, or else the message "Not logged in." To delete the account that you are currently logged in on, input "delete". To see all of the messages that you have sent to other users that have not yet recieved your messages (those users are currently logged out), input "list_pending".
The exact format for client input on the command line is shown below. If you send a message to a user who is not logged in, they will see that message immediately when they login.


Input Rules:
Usernames and passwords should not contain spaces. Usernames and passwords should each be <= 50 characters long.
Any messages sent to another user should be 280 characters or fewer. 

Input formats:
```
create <username> password>
login <username> <password>
logout
list <regex>
delete
status
list
send <username> <message>
list_pending
```

### gRPC vs non-gRPC
To run the ChatServer using gRPC, ``cd ChatgRPC`` before starting up the server and client.
To run the ChatServer without using gRPC, ``cd ChatPython`` before starting up the server and client.

### Testing
To run tests for the ChatServer with and without using gRPC, navigate to the appropriate folder (``ChatgRPC`` or ``ChatPython``, respectively) and run ``python3 tests.py``.