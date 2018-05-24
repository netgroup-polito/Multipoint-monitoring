#!/usr/bin/env python

import sys
import time 
import networkx as nx
import matplotlib.pyplot as plt
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from mininet.util import irange,dumpNodeConnections
from mininet.log import setLogLevel
from time import sleep

#array with ip address for each host in the topology
arrayIpHost=[]
#array with host_id for each host in the topology
arrayHost=[] 
#costant variable used in the script in order to add the T switch  
N=100  
#variable used in order to count the numer of links between switch T and switch S in the topology
NumLinkTS=0
#variable used in order to count the numer of links between host H and switch T in the topology
NumLinkHT=0
#variable used in order to count the numer of links between switches S in the topology
NumLinkSS=0
         
def myNetwork():
	
	#number of switch S in the topology
	n_switchs=0
	#number of links between switch S in the topology
	n_links=0

	global arrayIpHost
	global arrayHost	
	global NumLinkHT,NumLinkSS,NumLinkTS
	
	G = nx.read_graphml('Geant2012.graphml',str)
	
	print("Graph %s has %d nodes with %d edges"
          % (G.name, nx.number_of_nodes(G), nx.number_of_edges(G)))
          
	n_switchs=nx.number_of_nodes(G)
	n_links=nx.number_of_edges(G)
	
	net = Mininet( topo=None,link=TCLink,
	autoStaticArp=True,
                   build=False,
                   ipBase='10.0.0.0/8')

	info( '*** Adding controller \n' )
	c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

	info( '*** Add switches S \n')
	for switch in G.nodes_iter():
		switch_id="s"+str(int(switch)+1)
		id_node=int(int(switch)+1)
		s=net.addSwitch(switch_id,dpid=hex(id_node)[2:],cls=OVSKernelSwitch)
		print "Switch S :",s
		
	info( '*** Add switches T \n')
	for switch in G.nodes_iter():
		val=int(int(switch)+1)+N
		switch_id="s"+str(val)
		id_node=int(int(switch)+1)
		t=net.addSwitch(switch_id,cls=OVSKernelSwitch)
		print "Switch T:",t	

	info( '*** Add hosts H \n')
	for host in G.nodes_iter(data = True):
		host_id="h"+str(int(host[0])+1)
		ris=int(int(host[0])+1)+ int(10)
		host_mac="00:00:00:00:00:"+str(ris)
		host_ip="10.0.0."+str(int(host[0])+1)
		h=net.addHost(host_id,cls=Host,ip=host_ip,mac=host_mac,defaultRoute=None)
		print "Host H :",h	
		#if host[1]['label']=='Milan':
			#print "Country is Milan"
			#IP_Italy=host_ip
			#MAC_Italy=host_mac
			#print "IP IT",IP_Italy
			#print "MAC IT",MAC_Italy
		print "Host MAC:",host_mac
		print "Host IP:",host_ip
		arrayIpHost.append(host_ip)	
		arrayHost.append(h)

	info( '*** Add links between switch S \n')
	for edge in G.edges_iter():
		edge0_id="s"+str(int(edge[0])+1)
		edge1_id="s"+str(int(edge[1])+1)
		print "Add Links between switch S : ",edge0_id," and ",edge1_id
		net.addLink(edge0_id,edge1_id)
		NumLinkSS=NumLinkSS+1
	print "Tot Link between switch S : ",NumLinkSS
	
	info( '*** Add links between switch S and switch T \n')	
	for nod in G.nodes_iter():
		val=int(int(nod)+1)+N			
		tswitch_ID="s"+str(val)
		switch_ID="s"+str(int(nod)+1)
		port1=2
		port2=52
		net.addLink(tswitch_ID,switch_ID,port1,port2)
		print "Add Links between S and T : ",tswitch_ID," and ",switch_ID
		NumLinkTS=NumLinkTS+1
	print "Tot Link between switch S and switch T : ",NumLinkTS		
		
	info( '*** Add links between host H and switch T \n')	
	for hos in G.nodes_iter():
		val=int(int(hos)+1)+N			
		host_ID="h"+str(int(hos)+1)
		tswitch_ID="s"+str(val)
		port1=51
		port2=1
		net.addLink(host_ID,tswitch_ID,port1,port2)
		print "Add Links between host and T : ",host_ID," and ",tswitch_ID	
		NumLinkHT=NumLinkHT+1
	print "Tot Link between switch T and host H : ",NumLinkHT
								
	info( '*** Starting network\n')
	net.build()
				
	info( '*** Starting controllers\n')	
	for controller in net.controllers:
		controller.start()
		
	info( '*** Starting switches S\n')
	for sw in G.nodes_iter():	
		s_id="s"+str(int(sw)+1)
		net.get(s_id).start([c0])
		
	info( '*** Starting switches T\n')
	for sw in G.nodes_iter():	
		w=int(int(sw)+1)+N
		s_id="s"+str(w)
		net.get(s_id).start([c0])	
	
		
	#time.sleep(150)	
	time.sleep(90)
	#time.sleep(60)
	#time.sleep(50)
	
	print "Testing net connectivity"
	   
	H1=arrayHost[0]
	H1.cmd('rm -r /tmp/pnpm')
	H1.cmd('screen -d -m python -m trace -t /home/fmesolella/Desktop/Server.py'+" "+str(H1.IP())+" ")
			
	for h in net.hosts:	
		print "Host Source : ",h
		arrayIpHost.remove(h.IP())
		print "Host Destination : ",arrayIpHost
		s=""
		for h1 in arrayIpHost:
			s=s+h1+" "
		arrayIpHost.append(h.IP())
		h.cmd('python /home/fmesolella/Desktop/Client.py'+" "+str(H1.IP())+" "+str(h.IP())+" "+str(s)+" >> error.log 2>&1 &")
														
							
	CLI(net)			
	net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

