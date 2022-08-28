import socket
import struct
import sys


class SenderClient:
    def __init__(self, starter=b'\x20\x22\x06\x05', tailer=b'\xff\xff\xff\xff'):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.starter = starter
        self.tailer = tailer

    def connect_server(self, ipaddr='127.0.0.1', port=9997):
        self.sock.connect((ipaddr, port))

    def send_msg(self, sock, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        sock.send(msg)
        
    def send_filename(self, sock, filenmae):
        sock.send(filename)

    def send_starter(self, sock):
        sock.send(self.starter)

    def send_tailer(self, sock):
        sock.send(self.tailer)

    def close_session(self, sock):
        sock.close()

# if __name__ == "__main__":
    # #fpath = r'./data.csv'
    # sender = SenderClient()
    # sender.connect_server('47.108.64.28', 9997)
    # #sender.connect_server()
    # sender.send_starter(sender.sock)
    # print(sender.sock.recv(1024).decode('utf-8'))
    # fpath = sys.argv[1]
    # print(fpath)
    # f = open(fpath, 'rb')
    # datastream = f.read(10240)
    # while (datastream != b''):
        # sender.send_msg(sender.sock, datastream)
        # datastream = f.read(10240)
    # f.close()
    # #print('file end')
    # sender.send_tailer(sender.sock)
    # #print('tailer sent')
    # sender.close_session(sender.sock)
    
    
###transmit the file name in the stream    
if __name__ == "__main__":
    #fpath = r'./data.csv'
    sender = SenderClient()
    sender.connect_server('47.108.64.28', 9997)
    #sender.connect_server()
    sender.send_starter(sender.sock)
    print(sender.sock.recv(1024).decode('utf-8'))
    fpath = sys.argv[1]
    print(fpath)
    f = open(fpath, 'rb')
    filename=fpath.split('/')[-1]
    filename = filename.encode('utf-8')+(100-len(filename))*b'-'
    sender.send_msg(sender.sock, filename)
    datastream = f.read(10240)
    while (datastream != b''):
        sender.send_msg(sender.sock, datastream)
        datastream = f.read(10240)
    f.close()
    #print('file end')
    sender.send_tailer(sender.sock)
    #print('tailer sent')
    sender.close_session(sender.sock)
