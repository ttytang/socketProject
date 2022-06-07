import socket
import struct
import threading

class ReceiverClient:
    def __init__(self, starter=b'\x20\x22\x06\x05', tailer=b'\xff\xff\xff\xff'):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.starter = starter
        self.tailer = tailer
        self.tailer_flag = False
        self.stream_buffer = []
        self.session_size = 0
        self.stream_num = 0
        self.burst_num = 0

    def reset(self):
        self.tailer_flag = False
        self.stream_buffer = []
        self.session_size = 0
        self.stream_num = 0
        self.burst_num = 0

    def send_starter(self, sock):
        sock.send(self.starter)

    def connect_server(self, ipaddr='127.0.0.1', port=9998):
        self.sock.connect((ipaddr, port))

    def close_session(self, sock):
        sock.close()

    def receive_burst(self, sock):
        session_size = 0
        burst_num = 0
        fetch_buffer = b''
        stream_num = 0
        to_resolve_header = True
        while(not self.tailer_flag):
            one_fetch = sock.recv(1024000)
            burst_num += 1
            if not one_fetch:
                print("error on link when receiving message")
                self.close_session(sock)
                return None
            fetch_buffer = fetch_buffer + one_fetch
            while((not to_resolve_header and len(fetch_buffer) > 0) or (to_resolve_header and len(fetch_buffer) >= 4)):
                if (to_resolve_header): # to resolve header
                    msg_header = fetch_buffer[:4]
                    if (msg_header == self.tailer):
                        self.close_session(sock)
                        self.session_size = session_size
                        print("receive file size is %d" % (session_size - 100))
                        self.burst_num = burst_num
                        self.stream_num = stream_num
                        self.tailer_flag = True
                        break
                    msg_len = struct.unpack('>I', fetch_buffer[:4])[0]
                    to_resolve_header = False
                    to_be_fill_size = msg_len
                    if (len(fetch_buffer) == 4):
                        fetch_buffer = b''
                        #break
                    else:#len(fetch_buffer)>4
                        fetch_buffer = fetch_buffer[4:]
                else:# to resolve data
                    if (len(fetch_buffer) <= to_be_fill_size):
                        self.stream_buffer.append(fetch_buffer)
                        session_size += len(fetch_buffer)
                        to_be_fill_size = to_be_fill_size - len(fetch_buffer)
                        fetch_buffer = b''
                        if (to_be_fill_size):
                            to_resolve_header = False
                        else:
                            stream_num += 1
                            to_resolve_header = True
                    else:
                        self.stream_buffer.append(fetch_buffer[:to_be_fill_size])
                        session_size += to_be_fill_size
                        fetch_buffer = fetch_buffer[to_be_fill_size:]
                        stream_num += 1
                        to_resolve_header = True

    def receive_session(self, sock):
        session_size = 0
        stream_num = 0
        while(not self.tailer_flag):
            msg_header = sock.recv(len(self.tailer), socket.MSG_WAITALL)
            if not msg_header:
                print("error on link when receiving message header")
                self.close_session(sock)
                return None
            if (msg_header != self.tailer):
                msg_len = struct.unpack('>I', msg_header)[0]
                msg_payload = sock.recv(msg_len, socket.MSG_WAITALL)
                if not msg_payload:
                    print("error on link when receiving message payload")
                    self.close_session(sock)
                    return None
                self.stream_buffer.append(msg_payload)
                session_size += msg_len
                stream_num += 1
            else:
                self.close_session(sock)
                self.session_size = session_size
                print("forward session size %d" % session_size)
                self.stream_num = stream_num
                self.tailer_flag = True

# if __name__ == "__main__":
    # receiver = ReceiverClient()
    # receiver.connect_server('47.108.64.28', 9998)
    # #receiver.connect_server()
    # receiver.send_starter(receiver.sock)
    # #create a thread to receive stream
    # t = threading.Thread(target=receiver.receive_burst, args=(receiver.sock,))
    # t.start()
    # fpath = r'./forward_data.csv'
    # f = open(fpath, 'wb')
    # #while(receiver.stream_buffer or not receiver.stream_num):
    # while(receiver.stream_buffer or not receiver.tailer_flag):
        # if (receiver.stream_buffer):
            # f.write(receiver.stream_buffer.pop(0))
    # f.close()
    # receiver.reset()


### receive the file name in the stream    
if __name__ == "__main__":
    receiver = ReceiverClient()
    receiver.connect_server('47.108.64.28', 9998)
    #receiver.connect_server()
    receiver.send_starter(receiver.sock)
    #create a thread to receive stream
    t = threading.Thread(target=receiver.receive_burst, args=(receiver.sock,))
    t.start()
    # fpath = r'./forward_data.csv'
    # f = open(fpath, 'wb')
    #while(receiver.stream_buffer or not receiver.stream_num):
    head_seg = b''
    got_filename = False
    while(receiver.stream_buffer or not receiver.tailer_flag):
        if (receiver.stream_buffer):
            one_seg = receiver.stream_buffer.pop(0)
            if (not got_filename):
                head_seg += one_seg
                if(len(head_seg)<=100):
                    continue
                else:
                    fpath = head_seg[:100].decode('utf-8').split('-')[0]
                    f = open(fpath, 'wb')
                    f.write(head_seg[100:])
                    got_filename = True
            else:
                f.write(one_seg)
    f.close()
    receiver.reset()

