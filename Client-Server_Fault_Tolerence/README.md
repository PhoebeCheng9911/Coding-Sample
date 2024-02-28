# Client-Server Chat Application - Persistent and 2-fault tolerant

We modify an existing client-server chat application to make it persistent and 2-fault tolerant. We choose to modify the non-gRPC
chat application from Design Exercise 1, as this application is more straightforward to debug than the gRPC-based chat application.

## Persistence

Data Description: We persist information about the usernames and passwords of existing user accounts, and any messages that have been sent but not received. This information is stored in the subfolder ```data/``` across one json file for pending messages, and one json file for user information.

Updates Policy: We update the json files whenever the server's state space changes such that the username, password, or pending messages data has changed.
The user information json is updated whenever the client sends a create account message or a delete account message.
The pending messages json is updated whenever a pending message is delivered, a message is sent to a user who is not currently logged in, or a user account is deleted and there were messages pending delivery to the deleted account. 

This update policy ensures that whenever a server replica crashes/fails, the most up-to-date user information and pending messages is already persisted.

Initialization: When a server instance starts up, it loads user info and pending messages data if their corresponding json files exist. Otherwise, it initializes state with no known users and no pending messages.

## 2-fault tolerant
### Functionality
We support 2-fault tolerance for crash/failstop failures, which means that we require 3 server replicas. If up to 2 of these server replicas crash/failstop, then the client(s) will still be able to successfully connect and send messages through the remaining server replica. 

The server replicas can be hosted on the same machine or on different machines, and they will result in a 2-fault tolerant system regardless. 

### Implementation
The client deterministically orders the three server replicas based on the order of the host/port pairs passed in as input to the client instance. 
The client maintains internally the identity of the leader server. 
The client sends each message to all three server replicas. 
    If, while sending messages to a server replica, the client detects that that server replica has crashed/failed, it will record internally that this replica has failed. If the given replica was the current "leader," then the client will 
    assign the next-lowest indexed live server replica as the new "leader" by updating the client's internal state. 
    The client only processes/prints messages received by the "leader" server replica. This avoids the client printing out server
    responses in triplicate when all replicas are live. 

## User instructions
Use one terminal for each server replica instance, and one additional terminal for each connected client. 
Each server instance takes as input the host and port that it should listen on. 
Each client instance takes as input the hosts and ports of the 3 server replicas in the system. 

To start the server
```
python3 server.py [string: host1] [int: port1]
```
To start a client
```
python3 client.py [host1] [port1] [host2] [port2] [host3] [port3]
```

To determine the ip (HOST) of your local machine on Mac,
```ipconfig getifaddr en0```

For example, run the following lines in 4 separate terminals.
```
python3 server.py <HOST> 65433
python3 server.py <HOST> 65434
python3 server.py <HOST> 65435
python3 client.py 10.250.148.228 65433 10.250.148.228 65434 127.0.0.1 65435
```


## Testing
To run unit tests for the ChatServer, run ``python3 tests.py``.