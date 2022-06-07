#!/usr/bin/python3 -u
import os.path
import socket
import threading
import senderclient
import receiverclient
import struct
import time

class ReceiverServer(receiverclient.ReceiverClient):

    def __init__(self, starter=b'\x20\x22\x06\x05', tailer=b'\xff\xff\xff\xff'):
        super(ReceiverServer, self).__init__(starter=starter, tailer=tailer)
        self.data_sock = None
        self.data_ip = None
        
    def reset(self):
        super(ReceiverServer, self).reset()
        self.data_sock = None
        self.data_ip = None
        
    def binding(self, receiver_addr=('127.0.0.1', 9997)):
        self.sock.bind(receiver_addr)

    def listening(self, link_num = 5):
        self.sock.listen(link_num)

    ###def connection_ready(self):
    ###    sock, addr = self.sock.accept()
    ###    print('One sender is connecting from %s:%s...' % addr)
    ###    time.sleep(1)
    ###    try:
    ###       starter = sock.recv(len(self.starter), socket.MSG_DONTWAIT)
    ###       if (starter != self.starter):
    ###           return sock, None
    ###    except BlockingIOError:
    ###        return sock, None
    ###    print('Accept a new sender connection from %s:%s...' % addr)
    ###    return sock, addr
        
    def connection_ready(self):
        while(not self.data_ip):
            sock, addr = self.sock.accept()
            print('One sender is connecting from %s:%s...' % addr)
            time.sleep(1)
            try:
                starter = sock.recv(len(self.starter), socket.MSG_DONTWAIT)
                if (starter != self.starter):
                    self.close_session(sock)
                    continue
            except BlockingIOError:
                self.close_session(sock)
                continue
            print('Accept a new sender connection from %s:%s...' % addr)
            self.data_sock = sock
            self.data_ip = addr

    def send_warm_message(self, sock, addr, warm_message = b'Welcome'):
        print('Welcome %s:%s...' % addr)
        sock.send(warm_message)

    def link_handle(self, sock, addr, warm_message = b'Welcome'):
        self.send_warm_message(sock, addr, warm_message)
        self.receive_session(sock)
        #self.receive_burst(sock)


###used for testing receiver server on forward server
###if __name__ == "__main__":
###    receiver = ReceiverServer()
###    receiver.binding()
###    receiver.listening()
###    while True:
###        #create a thread to receive stream
###        trans_sock, source_ip = receiver.connection_ready()
###        t = threading.Thread(target=receiver.link_handle, args=(trans_sock, source_ip, b'Welcome'))
###        t.start()
###        if (not os.path.isfile(r'./forward_data.csv')):
###            fpath = r'./forward_data.csv'
###            f = open(fpath, 'wb')
###            while(receiver.stream_buffer or not receiver.stream_num):
###                if (receiver.stream_buffer):
###                    f.write(receiver.stream_buffer.pop(0))
###            print('session write complete!')
###            f.close()
###            receiver.reset()
###
class SenderServer(senderclient.SenderClient):

    def __init__(self, starter=b'\x20\x22\x06\x05', tailer=b'\xff\xff\xff\xff'):
        super(SenderServer, self).__init__(starter=starter, tailer=tailer)
        self.data_sock = None
        self.data_ip = None
        
    def reset(self):
        self.data_sock = None
        self.data_ip = None        

    def binding(self, sender_addr=('127.0.0.1', 9998)):
        self.sock.bind(sender_addr)

    def listening(self, link_num=5):
        self.sock.listen(link_num)
    
    def connection_ready(self):
        while(not self.data_ip):
            sock, addr = self.sock.accept()
            print('One receiver is connecting from %s:%s...' % addr)
            time.sleep(1)
            try:
                starter = sock.recv(len(self.starter), socket.MSG_DONTWAIT)
                if (starter != self.starter):
                    self.close_session(sock)
                    continue
            except BlockingIOError:
                self.close_session(sock)
                continue
            print('Accept a new receiver connection from %s:%s...' % addr)
            self.data_sock = sock
            self.data_ip = addr

    def send_warm_message(self, sock, addr, warm_message=b'Welcome'):
        print('Welcome %s:%s...' % addr)
        sock.send(warm_message)

    def link_handle(self, sock, message):
        self.send_msg(sock, message)

if __name__ == "__main__":
    receiver = ReceiverServer()
    receiver.binding(('0.0.0.0',9997))
    receiver.listening()
    sender = SenderServer()
    sender.binding(('0.0.0.0',9998))
    sender.listening()
    ###while True:
    ###    sender_sock, destin_ip = sender.connection_ready()
    ###    if (not destin_ip):
    ###        sender.close_session(sender_sock)
    ###        continue# means destionation receiver needs to open for the first
    ###    #create a thread to receive stream
    ###    receiver_sock, source_ip = receiver.connection_ready()
    ###    if (not source_ip):
    ###        receiver.close_session(receiver_sock)
    ###        continue
    ###    t = threading.Thread(target=receiver.link_handle, args=(receiver_sock, source_ip, b'Welcome'))
    ###    t.start()
    ###    #while(receiver.stream_buffer or not receiver.stream_num):
    ###    while(receiver.stream_buffer or not receiver.tailer_flag):
    ###        if (receiver.stream_buffer):
    ###            sender.send_msg(sender_sock, receiver.stream_buffer.pop(0))
    ###    sender.send_tailer(sender_sock)
    ###    sender.close_session(sender_sock)
    ###    receiver.reset()
    ###    print('session write complete!(9')
        
    while True:
        s = threading.Thread(target=sender.connection_ready)
        s.start()
        #create a thread to receive stream
        receiver.connection_ready()
        receiver_sock = receiver.data_sock
        source_ip = receiver.data_ip
        s.join()#wait destination receiver ready
        sender_sock = sender.data_sock
        destin_ip = sender.data_ip
        t = threading.Thread(target=receiver.link_handle, args=(receiver_sock, source_ip, b'Welcome'))
        t.start()
        #while(receiver.stream_buffer or not receiver.stream_num):
        while(receiver.stream_buffer or not receiver.tailer_flag):
            if (receiver.stream_buffer):
                sender.send_msg(sender_sock, receiver.stream_buffer.pop(0))
        sender.send_tailer(sender_sock)
        sender.close_session(sender_sock)
        receiver.reset()
        sender.reset()
        print('session write complete!(9')

###used only the receiver
###if __name__ == "__main__":
###    receiver = ReceiverServer()
###    receiver.binding()
###    receiver.listening()
###    while True:
###        #create a thread to receive stream
###        trans_sock, source_ip = receiver.connection_ready()
###        t = threading.Thread(target=receiver.link_handle, args=(trans_sock, source_ip, b'Welcome'))
###        t.start()
###        if (not os.path.isfile(r'./forward_data.csv')):
###            fpath = r'./forward_data.csv'
###            f = open(fpath, 'wb')
###            while(receiver.stream_buffer or not receiver.stream_num):
###                if (receiver.stream_buffer):
###                    f.write(receiver.stream_buffer.pop(0))
###            print('session write complete!')
###            f.close()
###            receiver.reset()
