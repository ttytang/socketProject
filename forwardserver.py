#!/usr/bin/env -S python3 -u
import os.path
import socket
import threading
import senderclient
import receiverclient
import struct
import time

import logging
import sys
class CustomFormatter(logging.Formatter):
   '''Logging Formatter to add colors and count warning / errors'''
   grey = '\x1b[38;21m'
   yellow = '\x1b[33;21m'
   red = '\x1b[31;21m'
   bold_red = '\x1b[31;1m'
   reset = '\x1b[0m'
   format = '%(asctime)s - %(message)s (%(filename)s:%(lineno)d) - %(name)s - %(levelname)s' 
   
   FORMATS = {
       logging.DEBUG: grey+format+reset,
       logging.INFO: grey+format+reset,
       logging.WARNING: yellow+format+reset,
       logging.ERROR: red+format+reset,
       logging.CRITICAL: bold_red+format+reset
   }

   def format(self, record):
       log_fmt = self.FORMATS.get(record.levelno)
       formatter = logging.Formatter(log_fmt)
       return formatter.format(record)

#create logger with 'spam_application'
logger = logging.getLogger('Forward')

#create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

if len(sys.argv)>1:
    if sys.argv[1] == 'color':
        ch.setFormatter(CustomFormatter())

if len(sys.argv)>2:
    logger.setLevel(logging.__getattribute__(sys.argv[2]))
else:
    logger.setLevel(logging.DEBUG)

logger.addHandler(ch)


class ReceiverServer(receiverclient.ReceiverClient):

    def __init__(self, starter=b'\x20\x22\x06\x05', tailer=b'\xff\xff\xff\xff'):
        super(ReceiverServer, self).__init__(starter=starter, tailer=tailer)
        self.data_sock = None
        self.data_ip = None
        self.lock = False
        
    def reset(self):
        super(ReceiverServer, self).reset()
        self.data_sock = None
        self.data_ip = None
        self.lock = False
        
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
        while(True):
            sock, addr = self.sock.accept()
            #print('One sender is connecting from %s:%s...' % addr)
            logger.info('One sender is connecting from %s:%s...' % addr)
            if (self.lock):
                self.close_session(sock)
                logger.info('Someone is sending, retry later!')
            else:
                time.sleep(1)
                try:
                    starter = sock.recv(len(self.starter), socket.MSG_DONTWAIT)
                    if (starter != self.starter):
                        self.close_session(sock)
                        continue
                #except BlockingIOError:
                except Exception as e:
                    self.close_session(sock)
                    logger.warning('%s:%s'%(e.__class__.__name__,e))
                    continue
                logger.info('Accept a new sender connection from %s:%s...' % addr)
                self.data_sock = sock
                self.data_ip = addr
                self.lock = True

    def remote_closed_check(self):
        while(True):
            #if (self.lock and not getattr(self.data_sock, '_closed')):
            if (self.data_sock and not getattr(self.data_sock, '_closed')):
                one_peek = self.data_sock.recv(1, socket.MSG_PEEK)
                if not one_peek:
                    #self.reset()
                    self.tailer_flag = True
                    time.sleep(1)
                    self.close_session(self.data_sock)

    def send_warm_message(self, sock, addr, warm_message = b'Welcome'):
        logger.info('Welcome %s:%s...' % addr)
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
        self.lock = False
        
    def reset(self):
        self.data_sock = None
        self.data_ip = None        
        self.lock = False

    def binding(self, sender_addr=('127.0.0.1', 9998)):
        self.sock.bind(sender_addr)

    def listening(self, link_num=5):
        self.sock.listen(link_num)
    
    def connection_ready(self):
        while(True):
            sock, addr = self.sock.accept()
            logger.info('One receiver is connecting from %s:%s...' % addr)
            if (self.lock):
                self.close_session(sock)
                logger.info('Someone is receiving, retry later!')
            else:
                time.sleep(1)
                try:
                    starter = sock.recv(len(self.starter), socket.MSG_DONTWAIT)
                    if (starter != self.starter):
                        self.close_session(sock)
                        continue
                #except BlockingIOError:
                except Exception as e:
                    self.close_session(sock)
                    logger.warning('%s:%s'%(e.__class__.__name__,e))
                    continue
                logger.info('Accept a new receiver connection from %s:%s...' % addr)
                self.data_sock = sock
                self.data_ip = addr
                self.lock = True

    def remote_closed_check(self):
        while(True):
            #if(self.lock):
            if(self.data_sock):
               try:
                   logger.debug('when coming, the data sock is:%s'%self.data_sock)
                   one_peek = self.data_sock.recv(1, socket.MSG_PEEK)
                   if not one_peek:
                       logger.warning('detect receiver client close the connection or sender server close the connection to cause sock.recv return IMMEDIATELY with:%s'%one_peek)
                       if (self.data_sock) and (not getattr(self.data_sock, '_closed')):
                           self.close_session(self.data_sock)
                           self.reset()
                           #self.lock = False
               #except (AttributeError, IOError, OSError) as e:
               except Exception as e:
                   logger.warning('%s:%s'%(e.__class__.__name__,e))
                   #print ('may be not sever fault')
                   #print('receive msg on server actively closed socket')
            #time.sleep(10)
    
    ###def remote_closed_check(self):
    ###    while(True):
    ###        #if (self.lock and not getattr(self.data_sock, '_closed')):
    ###        if (self.data_sock and not getattr(self.data_sock, '_closed')):
    ###            one_peek = self.data_sock.recv(1, socket.MSG_PEEK)
    ###            if not one_peek:
    ###                #self.reset()
    ###                #time.sleep(1)
    ###                self.close_session(self.data_sock)
    ###            time.sleep(10)

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
        
    s = threading.Thread(target=sender.connection_ready)
    s.start()
    r = threading.Thread(target=receiver.connection_ready)
    r.start()
    sc = threading.Thread(target=sender.remote_closed_check)
    sc.start()
    #rc = threading.Thread(target=receiver.remote_closed_check)
    #rc.start()
    while True:
        if (receiver.data_ip and sender.data_ip):
            #create a thread to receive stream
            t = threading.Thread(target=receiver.link_handle, args=(receiver.data_sock, receiver.data_ip, b'Welcome'))
            t.start()
            try:
                while sender.data_sock and (receiver.stream_buffer or not receiver.tailer_flag):
                    if (receiver.stream_buffer):
                        sender.send_msg(sender.data_sock, receiver.stream_buffer.pop(0))
                sender.send_tailer(sender.data_sock)
                sender.close_session(sender.data_sock)
                #logger.warning('just close sender socket and prepare reset sender socket')
                sender.reset()
            #except (AttributeError, IOError, OSError) as e:
            except Exception as e:
                logger.warning('%s:%s'%(e.__class__.__name__,e))
                #print('send msg on closed socket')
                #receiver.close_session(receiver.data_sock)
                if not getattr(receiver.data_sock,'_closed'):
                    receiver.tailer_flag = True
            finally:
                while not getattr(receiver.data_sock, '_closed'):
                    logger.debug('wait for receiver server data socket close to reset receiver')
                receiver.reset()
                logger.info('session complete!(v to wait next session')

###used only the receiver
###if __name__ == "__main__":
###    receiver = ReceiverServer()
###    receiver.binding()
###    receiver.listening()
###    while True:
###        #create a thread to receive stream
###        trans_sock, source_ip = receiver.connection_ready()
###        t = threading.Thread(target=receiver.link_handle, args=(trans_sock, source_ip, b'Welcome'))
###        t.sart()
###        if (not os.path.isfile(r'./forward_data.csv')):
###            fpath = r'./forward_data.csv'
###            f = open(fpath, 'wb')
###            while(receiver.stream_buffer or not receiver.stream_num):
###                if (receiver.stream_buffer):
###                    f.write(receiver.stream_buffer.pop(0))
###            print('session write complete!')
###            f.close()
###            receiver.reset()
