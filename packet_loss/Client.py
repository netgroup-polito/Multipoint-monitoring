#!/usr/bin/python2.7

import zmq
import sys
import socket
import errno
import select
from time import sleep
from multiprocessing import Process, Value

class Type:
    SYN = 1
    FIN = 2
    SENT = 3
    RECV = 4

# Packet size 42B= 336b
NUM_PKTS= 1000*5
TEST_DURATION= 60*5
UDP_PORT=6666
SERVER_PORT=5555
server_ip = ''
# Time to wait for pending packets
TIMEOUT = 60

def client():
    
    global server_ip
        
    data={}
    server_ip=sys.argv[1]
    host=sys.argv[2]
    dests=set(sys.argv[3:])
    
    context = zmq.Context()
    zmq_skt = context.socket(zmq.PUSH)
    zmq_skt.connect("ipc:///tmp/pnpm")
    
    # Connect
    data['type']= Type.SYN
    data['source']=host
    zmq_skt.send_pyobj(data)
    data.clear()
    
    stop = Value('i', 0)
    
    receiver_p = Process(target=receiver, args=(stop,host))
    receiver_p.start()
    sleep(10)
    sender_p = Process(target=sender, args=(dests,host))
    sender_p.start()
    sender_p.join()
    
    sleep(TIMEOUT)
    stop.value=1
    receiver_p.join()
    
    # Disconnect
    data['type']= Type.FIN
    data['source']=host
    data['entries']=len(dests)
    zmq_skt.send_pyobj(data)
    data.clear()
    zmq_skt.close()

def sender(dests,host):
    
    global server_ip    
    num_sent={}
    for d in dests:
        num_sent[d]=0   
    interpacket_gap=1/(float(NUM_PKTS*len(dests))/float(TEST_DURATION))
    context = zmq.Context()
    zmq_skt = context.socket(zmq.PUSH)
    zmq_skt.connect("ipc:///tmp/pnpm")  
    udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    data={}   
    for i in xrange(0,NUM_PKTS):
        for d in dests:
            try:               
                try:
                    udp_sock.sendto("", (d,UDP_PORT))
                except socket.error as se:
                    #Ignore [Errno 101] Network is unreachable
                    if se.errno != errno.ENETUNREACH:
                        raise se                               
                num_sent[d]+=1                
                sleep(interpacket_gap)               
            except socket.error as se:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print("Socket error:  %s %s %s"%(se, exc_type, exc_tb.tb_lineno))               
                udp_sock.close()
                udp_sock=None
                return
    udp_sock.close()
    udp_sock=None    
    for d in dests:
        data['type']= Type.SENT
        data['from']=host
        data['to']=d
        data['sent']=num_sent[d]
        zmq_skt.send_pyobj(data)
        data.clear()   
    zmq_skt.close()
    
def receiver(stop,host):
    
    global server_ip    
    data={}
    context = zmq.Context()
    zmq_skt = context.socket(zmq.PUSH)
    zmq_skt.connect("ipc:///tmp/pnpm")   
    srcs={}
    udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_sock.bind((host, UDP_PORT))
    udp_sock.setblocking(0)   
    while (not stop.value):       
        ready = select.select([udp_sock], [], [], 10)       
        if ready[0]:
            msg, (src_ip, src_port) = udp_sock.recvfrom(1500) #Buffer size is 1500 bytes            
            if src_ip not in srcs:
                srcs[src_ip]=1
            else:
                srcs[src_ip]+=1       
    for s,r in srcs.iteritems():
        data['type']= Type.RECV
        data['from']=s
        data['to']=host
        data['recv']=r
        zmq_skt.send_pyobj(data)
        data.clear()






    
if __name__ == "__main__":
    client()
