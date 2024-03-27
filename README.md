# Distributed grpc Chat Application


### Usage
Use one terminal for the server, and one additional terminal for each connected client.
To start the server
```
python3 server.py
```
To start a client
```
python3 client.py
```
### Supported Client Actions
Clients can send messages to one another, as well as performing a variety of login/logout/status functions.

Input formats:
```
create <username> <password>
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
We implemented ChatServer with different empathsis. To run the simple ChatServer, ``cd ChatgRPC`` before starting up the server and client. 
To run the ChatServer using gRPC, ``cd ChatgRPC`` before starting up the server and client.
To run the ChatServer with Fault Tolerance, ``cd ChatPython`` before starting up the server and client.
