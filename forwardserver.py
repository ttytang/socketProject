#!/usr/bin/python3
import os.path
import socket
import threading
import senderclient
import receiverclient
import struct

class ReceiverServer(receiverclient.ReceiverClient):
        
    def binding(self, receiver_addr=('127.0.0.1', 9997)):
        self.sock.bind(receiver_addr)

    def listening(self, link_num = 5):
        self.sock.listen(link_num)

    def connection_ready(self):
        sock, addr = self.sock.accept()
        print('Accept new connection from %s:%s...' % addr)
        return sock, addr

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

    def binding(self, sender_addr=('127.0.0.1', 9998)):
        self.sock.bind(sender_addr)

    def listening(self, link_num=5):
        self.sock.listen(link_num)

    def connection_ready(self):
        sock, addr = self.sock.accept()
        print('Accept new connection from %s:%s...' % addr)
        return sock, addr

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
    while True:
        #create a thread to receive stream
        receiver_sock, source_ip = receiver.connection_ready()
        sender_sock, destin_ip = sender.connection_ready()
        t = threading.Thread(target=receiver.link_handle, args=(receiver_sock, source_ip, b'Welcome'))
        t.start()
        #while(receiver.stream_buffer or not receiver.stream_num):
        while(receiver.stream_buffer or not receiver.tailer_flag):
            if (receiver.stream_buffer):
                sender.send_msg(sender_sock, receiver.stream_buffer.pop(0))
        sender.send_tailer(sender_sock)
        sender.close_session(sender_sock)
        receiver.reset()
        print('session write complete!(8')

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
