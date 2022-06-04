import socket
import struct
import sys


class SenderClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_server(self, ipaddr='127.0.0.1', port=9997):
        self.sock.connect((ipaddr, port))

    def send_msg(self, sock, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        sock.send(msg)

    def send_tailer(self, sock, tailer=b'\xff\xff\xff\xff'):
        sock.send(tailer)

    def close_session(self, sock):
        sock.close()

if __name__ == "__main__":
    #fpath = r'./data.csv'
    sender = SenderClient()
    sender.connect_server('47.108.64.28', 9997)
    #sender.connect_server()
    print(sender.sock.recv(1024).decode('utf-8'))
    fpath = sys.argv[1]
    print(fpath)
    f = open(fpath, 'rb')
    datastream = f.read(10240)
    while (datastream != b''):
        sender.send_msg(sender.sock, datastream)
        datastream = f.read(10240)
    f.close()
    #print('file end')
    sender.send_tailer(sender.sock)
    #print('tailer sent')
    sender.close_session(sender.sock)