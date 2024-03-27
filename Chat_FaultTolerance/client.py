import socket
import fileinput
import codecs
import _thread
import sys
import errno

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65433  # The port used by the server
N_SERVERS = 3
verbose = False

# Reference for working with multiple machines
# https://stackoverflow.com/questions/11352855/communication-between-two-computers-using-python-socket


class Client:
    '''
    TODO: Maybe keep track of length of last message received from each server instance. 
    Then if 1st server conks out after reading 512 bytes, server 2 should print out the last 512-1024 bytes it received.
    '''
    def __init__(self, hosts,ports,out_file=None):
        self.out_file = out_file  # if not None, write output to file
        # TODO: create 3 sockets in self.s array, start 3 threads and give each thread the index of the server instance they're listening to
        # TODO: store index of which server we want to print from
        self.s = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(N_SERVERS)]
        self.replica_status = [False]*N_SERVERS
        for i in range(N_SERVERS):
            try:
                self.s[i].connect((hosts[i],ports[i]))
                if verbose:
                    print(f"Connected to server replica at {hosts[i]}::{ports[i]}")
                _thread.start_new_thread(self.receive, tuple([i]))
                self.replica_status[i]=True
            except:
                sys.exit(f"Failed to connect to server at {hosts[i]}::{ports[i]}")
        # set self.read_server_idx to the index of the first server that connected successfully
        self.read_server_idx = next((i for i, x in enumerate(self.replica_status) if x), None)

    def run(self):
        # for line in fileinput.input():
        for line in sys.stdin:
            self.sendline(line)
            if self.read_server_idx>=N_SERVERS:
                sys.exit()

    def sendline(self, line):  # send line length (without trailing newline), followed by line
        line_len = len(line.rstrip('\n'))
        for i in range(N_SERVERS):
            try:
                self.s[i].sendall(bytes(f'{line_len:>3}{line}', 'utf-8'))  # max message length is 280, so right-align length by 3
            except IOError as e:
                if e.errno == errno.EPIPE:
                    pass

    def receive(self,server_index):
        while True:
            try:
                data = self.s[server_index].recv(1024)
                self.s[server_index].sendall(bytes('','utf-8')) # throw exception if server is disconnected
                if data and self.read_server_idx==server_index:
                    if self.out_file:
                        with open(self.out_file, 'a') as f:
                            f.write(codecs.decode(data))
                    else:
                        print(codecs.decode(data), end='')
            except:
                if verbose:
                    print(f"Server replica {server_index} disconnected")
                # mark this current server as failed
                self.replica_status[server_index] = False
                # update index of earliest live server if needed
                if self.read_server_idx==server_index:
                    # record that the next live indexed server should be read from
                    self.read_server_idx = next((i for i, x in enumerate(self.replica_status) if x), N_SERVERS)
                    if self.read_server_idx>=N_SERVERS:
                        print("All server replicas failed, so the server crashed. Whoops!")
                sys.exit(f"Exit recv thread for server {server_index}")
                

def get_conn_info():
    hosts=[]
    ports=[]
    if (len(sys.argv) == 7):
        try:
            hosts = [sys.argv[1],sys.argv[3],sys.argv[5]]
            ports = [int(sys.argv[2]),int(sys.argv[4]),int(sys.argv[6])]
        except ValueError:
            sys.exit("ports must be integers")
    elif (len(sys.argv) == 1):
        hosts = [HOST for i in range(N_SERVERS)]
        ports = [PORT+i for i in range(N_SERVERS)]
    else:
        sys.exit("Usage: python3 client.py [host1] [port1] [host2] [port2] [host3] [port3]")
    return hosts,ports

if __name__ == "__main__":
    hosts,ports = get_conn_info()

    c = Client(hosts,ports)
    c.run()
