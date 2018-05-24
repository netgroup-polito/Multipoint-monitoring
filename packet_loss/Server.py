#!/usr/bin/python2.7

import zmq
import sys 

SERVER_PORT=5555
OUTPUT_FILE='results.dat'
SUMMARY_FILE='summary.dat'

class Type:
    SYN = 1
    FIN = 2
    SENT = 3
    RECV = 4
    
def server():
    
    try:
        server_ip=sys.argv[1]
        context = zmq.Context()
        receiver = context.socket(zmq.PULL)
        connected=[]
        disconnected=[]
        counters={}
        num_sent=0
        num_recv=0
        num_entries=0
        total_lost=0
        total_sent=0
        total_recv=0
        summary_lines=[]
        
        #receiver.bind("tcp://%s:%d"%(server_ip,SERVER_PORT))
        receiver.bind("ipc:///tmp/pnpm")
        
        summary_lines.append("Server listening on %s:%d"%(server_ip, SERVER_PORT))
    
        data = {}
    
        stop = False
        
        while not stop:
    
            data = receiver.recv_pyobj()
            
            if data['type']==Type.SYN:
                connected.append(data['source'])
                summary_lines.append ("%s connected"%data['source'])
                
            elif data['type']==Type.FIN:
                disconnected.append(data['source'])
                num_entries+=data['entries']
                summary_lines.append ("%s disconnected, %d entries"%(data['source'],data['entries']))
                
            elif data['type']==Type.SENT:
                
                if data['from'] not in counters:
                    counters[data['from']] = {}
                if data['to'] not in counters[data['from']]:
                    counters[data['from']][data['to']] = {}
    
                counters[data['from']][data['to']]['sent'] = data['sent']
                num_sent+=1
                
                summary_lines.append ("%s reported %d sent to %s"%(data['from'], data['sent'], data['to']))
            
            elif data['type']==Type.RECV:
                
                if data['from'] not in counters:
                    counters[data['from']] = {}
                if data['to'] not in counters[data['from']]:
                    counters[data['from']][data['to']] = {}
    
                counters[data['from']][data['to']]['recv'] = data['recv']
                num_recv+=1
                
                summary_lines.append ("%s reported %d received from %s"%(data['to'], data['recv'], data['from']))
            
            if sorted(connected)==sorted(disconnected) and num_entries==num_sent==num_recv:
                stop =True
        
        with open(OUTPUT_FILE, 'w') as outfile:
            
            for f, ts in counters.iteritems():
                for t, n in ts.iteritems():
                    if 'sent' not in n:
                        raise Exception("Sent report missing for %s\t%s\n"%(f,t))
                    if 'recv' not in n:
                        raise Exception("Recv report missing for %s\t%s\t%d\n"%(f,t,n['sent']))
                    
                    lost=n['sent']-n['recv']
                    outfile.write("%s\t%s\t%d\t%d\t%d\n"%(f,t,n['sent'],n['recv'],lost))
                    total_lost+=lost
                    total_sent+=n['sent']
                    total_recv+=n['recv']
    
        summary_lines.append ("Num entries: %d"%(num_entries))
        summary_lines.append ("Total sent: %d"%(total_sent))
        summary_lines.append ("Total recv: %d"%(total_recv))
        summary_lines.append ("Total lost: %d"%(total_lost))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        summary_lines.append("Exception %s %s %s"%(e, exc_type, exc_tb.tb_lineno))
    finally:
        with open(SUMMARY_FILE, 'w') as sfile:
            for l in summary_lines:
                sfile.write(l)
                sfile.write("\n")
server()
