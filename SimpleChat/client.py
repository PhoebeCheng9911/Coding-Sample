import socket
import fileinput
import codecs
import _thread

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65433  # The port used by the server


class Client:
    def __init__(self, out_file=None):
        self.out_file = out_file  # if not None, write output to file
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
        _thread.start_new_thread(self.receive, tuple())

    def run(self):
        for line in fileinput.input():
            self.sendline(line)

    def sendline(self, line):  # send line length (without trailing newline), followed by line
        line_len = len(line.rstrip('\n'))
        self.s.sendall(bytes(f'{line_len:>3}{line}', 'utf-8'))  # max message length is 280, so right-align length by 3

    def receive(self):
        while True:
            try:
                data = self.s.recv(1024)
                if data:
                    if self.out_file:
                        with open(self.out_file, 'a') as f:
                            f.write(codecs.decode(data))
                    else:
                        print(codecs.decode(data), end='')
            except:
                print("Server disconnected")


if __name__ == "__main__":
    c = Client()
    c.run()
