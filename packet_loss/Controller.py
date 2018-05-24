# Copyright 2017 Federica Mesolella
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

from pox.core import core
from pox.lib.revent import EventRemove
from pox.lib.addresses import IPAddr,EthAddr
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
from pox.openflow.of_json import *
from pox.lib.recoco import Timer
from pox.lib.revent import *  
from collections import defaultdict  
from threading import Thread, Lock
from pox.openflow.discovery import Discovery  
import pox.openflow.libopenflow_01 as of
import pox.openflow.nicira as nx
import pox.lib.packet as pkt
import networkx as NX
import socket
import time
import sys
import math 
import json
import signal
import threading

#count the number of matching rules inserted in switch S
num_ruleS=0
#count the number of matching rules inserted in switch T
num_ruleT=0
#variable to store the old value of dpid
old=0
#logger
log = core.getLogger()
#delay
_flood_delay = 0
#flag in the set function 
flag_set=1
#flag in the match function 
flag_match_S=0
#flag in the match function
flag_match_T=0
#flag in the read counter function
flag_read=0
#flag in the forwarding_high_priority function
flag_forward_hp=0
#flag in the forwarding_low_priority function
flag_forward_lp1=0
flag_forward_lp2=0
#flag in the set_port_in_TOS function
flag_set_port=0
#flag in the create_flow_stats_list function
flag_flow_stats=0
#counter in the set function 
C_set=0
#counter in the match function
C_match_S=0
#counter in the match function
C_match_T=0
#counter in the read counter function
C_read=0
#counter in the get_labels  function
C_get_labels=0
#counter in the forwarding_high_priority  function
C_forward_hp=0
#counter in the forwarding_low_priority  function
C_forward_lp1=0
C_forward_lp2=0
#counter in the set_port_in_TOS function
C_set_port=0
#counter in the create_flow_stats_list function
C_flow_stats=0
C_flow_stats_1=0
#counter used in the case of reading of flag 0 in the create_flow_stats_list function 
cont1=0
#counter used in the case of reading of flag 1 in the create_flow_stats_list function 
cont2=0
#counter in the link_event function
C_link_event=0
#costant to define the number of switch S in the topology
N=40
#costant useful to verify the end of link detection depends on the value of N
M=202
#costant variable used to create the mac address
Z=10
#variable used to read values foreach switch connected
VAR=0
#variable used to run once 
run_once=0
#variables used for traffic monitoring
ip_src=0
ip_dst=0
mac_src=0
mac_dst=0
#variable used for traffic monitoring
var1=0
var2=0
var3=0
var4=0	
#variables used to get switch informations
switch1_dpid=0
switch2_dpid=0
switch1_port=0
switch2_port=0
#array with port numbers
Array=[]
#array with shortest path foreach switch
AllShortPath=[]
#graph
G=[]
G = NX.Graph()
#variables with the sum of counters of all switch in the topology
sum_output1_port52=0
sum_input1_port52=0
sum_output0_port52=0
sum_input0_port52=0
#array with the counters in input and output of 52 port
Count_in1_PORT52=[0]*41
Count_out1_PORT52=[0]*41
Count_in0_PORT52=[0]*41
Count_out0_PORT52=[0]*41
#array with the counters in input and output ....  41x41=1681 
Count_in1_PORTS=[0]*1681
Count_out1_PORTS=[0]*1681
Count_in0_PORTS=[0]*1681
Count_out0_PORTS=[0]*1681
#array with the partial sum
somma_parziale_IN_0=[0] * 1681
somma_parziale_OUT_0=[0] * 1681
somma_parziale_IN_1=[0] * 1681
somma_parziale_OUT_1=[0] * 1681
#count the number of low priority rules inserted in all switch in the topology
count_rules_low_priority=0
Array_Country=[0]*41
dict1={}
dict2={}
#dictiionary with the Results printed on a json file 
Results=[]
#costants
port52=52
bit_value0=0
bit_value1=1
direct1="output"
direct2="input"
periodDiz=0	
period=0
				
class LearningSwitch (object):
  
  global G
   
  def __init__ (self, connection, transparent):
	
	self.connection = connection	
	self.transparent = transparent    	
	connection.addListeners(self)	
	self.hold_down_expired = _flood_delay == 0
		
  	#set flag TOS to 0 or 1 every T=N seconds 
	self._set_flag(60)
	#read the counters every T=N/2 seconds
	self._read_counters(30)
	#just once insert in the switches S the rules to match the packets with flag set to 0 or 1
	self._match_flag_S(40)
	#just once insert in the switches T the rules to forward packets
	self._forwarding_T(40)
	#just once insert in the switches S the rules in order to set the port number in the TOS field
	self._set_port_in_TOS_field(30)
	#just once insert in the switches S the forwarding rules with low priority 
	self._forwarding_low_priority(25)
	#get the labels of all nodes in the topology
	self._get_labels_from_topology(20)
	#just once insert in the switches S the forwarding rules with high priority 
	self._forwarding_high_priority(35)
					
  def _set_flag(self, dt):
	  
	  #every T=N second set bit TOS to 1 or 0
	  Timer(dt, self.set_bit, recurring=True)
		
  def _match_flag_S(self, dt):
	  
	  #Just once insert in the switches S the rules to match the bit/flag to 0 and 1 
	  Timer(dt, self.match_bit_S,recurring=False)	
	  	  		
  def _forwarding_T(self, dt):
	  
	  #Just once insert in the switches T the rules to match the bit/flag to 0 and 1
	  Timer(dt, self.forwarding_lowp_T,recurring=False)		
	
  def _read_counters(self,dt):
	  
	  #Listen for flow stats
	  core.openflow.addListenerByName("FlowStatsReceived",create_flow_stats_list)
	  #every T=N/2 seconds read the counters
	  Timer(dt, self.read_counter, recurring=True) 	
	  		
  def _set_port_in_TOS_field(self,dt):
	  	  
	  #just once insert in the switches S the rules in order to set the port number in the TOS field
	  Timer(dt, self.set_port_in_TOS, recurring=False)	
	  			
  def _forwarding_low_priority(self, dt):
	  
	  #just once insert in the switches S the forwarding rules with low priority
	  Timer(dt, self.forwarding_low_p, recurring=False) 
	  		
  def _get_labels_from_topology(self,dt):
	  	  	  
	  #get the labels of all nodes in the topology
	  Timer(dt, self.get_labels_nodes, recurring=False)
 
  def _forwarding_high_priority(self,dt):
	  	  
	  #just once insert in the switches S the forwarding rules with high priority 
	  Timer(dt, self.forwarding_high_p, recurring=False)	 



#rules forwarding low priority in switch T
  def  forwarding_rules_lowpriority_switchT(self):
	  
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 1
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	
	
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=2
	msg.priority = 1
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.actions.append(of.ofp_action_output(port = 1))
	self.connection.send(msg)	


#rules setting flag in swicth T
  def setting_flag_rule_in_switch_T_macs_macd_ips_ipd(self,tos):
	
	t=tos  
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	
		  
  def setting_flag_rule_in_switch_T_macs_macd(self,tos):
	
	t=tos 
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	
			  	
  def setting_flag_rule_in_switch_T_ips_ipd(self,tos):
	
	t=tos  
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	
	
  def setting_flag_rule_in_switch_T_macs_ips(self,tos):
	
	t=tos 
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)
		
  def setting_flag_rule_in_switch_T_macd_ipd(self,tos):
	
	t=tos 
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	
	
  def setting_flag_rule_in_switch_T(self,tos):
	
	t=tos 
	msg = nx.nx_flow_mod()
	msg.command = of.OFPFC_MODIFY
	msg.table_id = 0
	msg.match.in_port=1
	msg.priority = 10 
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_ip_proto = 17
	msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
	msg.actions.append(of.ofp_action_output(port = 2))
	self.connection.send(msg)	


#rules matching flag in swicth S	
  def matching_flag_rule_in_switchS_macs_macd_ips_ipd(self,port,tos):
	
	t=tos
	p=port  
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.match.of_ip_tos=t 
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)
	
  def matching_flag_rule_in_switchS_macs_macd(self,port,tos):
	
	t=tos
	p=port  
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_tos=t
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)
	  	  
  def matching_flag_rule_in_switchS_ips_ipd(self,port,tos):
	
	t=tos
	p=port   
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.match.of_ip_tos=t
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)
		
  def matching_flag_rule_in_switchS_macs_ips(self,port,tos):
	
	t=tos
	p=port   
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_src = EthAddr(mac_src)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_src = IPAddr(ip_src)
	msg.match.of_ip_tos=t
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)
	
  def matching_flag_rule_in_switchS_macd_ipd(self,port,tos):
	
	t=tos
	p=port  
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_eth_dst = EthAddr(mac_dst)
	msg.match.of_ip_proto = 17
	msg.match.of_ip_dst = IPAddr(ip_dst)
	msg.match.of_ip_tos=t
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)
					
  def matching_flag_rule_in_switchS(self,port,tos):
	
	t=tos
	p=port  
	msg = nx.nx_flow_mod()
	msg.table_id = 0
	msg.match.in_port=p
	msg.priority = 10
	msg.idle_timeout = of.OFP_FLOW_PERMANENT
	msg.hard_timeout = of.OFP_FLOW_PERMANENT
	msg.match.of_eth_type = pkt.ethernet.IP_TYPE
	msg.match.of_ip_proto = 17	
	msg.match.of_ip_tos=t
	msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 2))
	self.connection.send(msg)	    

	  				  	 			  	
  def set_bit(self):
	  
	  
	  if self.connection.dpid > 100:
		  	  
		localtime = time.asctime( time.localtime(time.time()) ) 
						       			  
		global flag_set		
		global N
		global C_set
		global VAR
		global ip_src, ip_dst, mac_src, mac_dst_
		global var1,var2,var3,var4
		
		C_set=C_set+1	
		
		msg = nx.nx_flow_mod_table_id()
		self.connection.send(msg)				
				
		if C_set==1:				
			VAR=1		
			if flag_set==0:		
				flag_set=1
			elif flag_set==1:		
				flag_set=0	
											 
		if flag_set==0:
									
			if var1==1 and var2==1 and var3==1 and var4==1:
				
				tos=0x04
				self.setting_flag_rule_in_switch_T_macs_macd_ips_ipd(tos)	
								
			elif var1==1 and var2==1:
				
				tos=0x04
				self.setting_flag_rule_in_switch_T_ips_ipd(tos)			
					
			elif var3==1 and var4==1:
								
				tos=0x04
				self.setting_flag_rule_in_switch_T_macs_macd(tos)			
					
			elif var1==1 and var3==1:
				
				tos=0x04
				self.setting_flag_rule_in_switch_T_macs_ips(tos)
								
			elif var2==1 and var4==1:
								
				tos=0x04
				self.setting_flag_rule_in_switch_T_macd_ipd(tos)
						
			else:
				
				print "Insert rules of setting in switch T start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_set					
				tos=0x04
				self.setting_flag_rule_in_switch_T(tos)
				
					 			
		elif flag_set==1:
				
			if var1==1 and var2==1 and var3==1 and var4==1:			
									
				tos=0
				self.setting_flag_rule_in_switch_T_macs_macd_ips_ipd(tos)
							
			elif var1==1 and var2==1:
									
				tos=0
				self.setting_flag_rule_in_switch_T_ips_ipd(tos)		
					
			elif var3==1 and var4==1:
									
				tos=0
				self.setting_flag_rule_in_switch_T_macs_macd(tos)
									
			elif var1==1 and var3==1:
									
				tos=0
				self.setting_flag_rule_in_switch_T_macs_ips(tos)
								
			elif var2==1 and var4==1:
												
				tos=0
				self.setting_flag_rule_in_switch_T_macd_ipd(tos)
			
			else:	
				
				print "Insert rules of setting in switch T  start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_set											
				tos=0
				self.setting_flag_rule_in_switch_T(tos)
			
		if C_set==N:
		 C_set=0					
	
  def match_bit_S(self):
	  
		localtime = time.asctime( time.localtime(time.time()) )
		 		       	  
		global flag_match_S
		global C_match_S
		global num_ruleS	
		global ip_src, ip_dst, mac_src, mac_dst	
		global var1,var2,var3,var4 
		
		ports = []
		ports_switch=[]		
		limit=65534 
			
		for m in self.connection.features.ports:
			ports.append(m.port_no)
		for element in ports:		
			if element < limit:
				ports_switch.append(element)		
		max = ports_switch[0] 
		pos = 1 
		while pos < len(ports_switch) : 
			if ports_switch[pos] > max : 
				max = ports_switch[pos] 
			pos = pos + 1 
		ports_switch.remove(max) 
	  
		if self.connection.dpid <=40: 
					
			C_match_S=C_match_S+1
						
			msg = nx.nx_flow_mod_table_id()
			self.connection.send(msg)
			
			if C_match_S==1:
				
				if flag_match_S==0:		
					flag_match_S=1
						
										
			if flag_match_S==1:
										
				if var1==1 and var2==1 and var3==1 and var4==1:
										
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS_macs_macd_ips_ipd(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS_macs_macd_ips_ipd(port,tos)		
				
					for p in ports_switch:
						porta=p	
												
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS_macs_macd_ips_ipd(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS_macs_macd_ips_ipd(port,tos)
								
					
				elif var1==1 and var2==1:
		
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS_ips_ipd(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS_ips_ipd(port,tos)	
				
					for p in ports_switch:
						porta=p		
						
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS_ips_ipd(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS_ips_ipd(port,tos)
											
				elif var3==1 and var4==1:
		
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS_macs_macd(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS_macs_macd(port,tos)
				
					for p in ports_switch:
						porta=p
						
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS_macs_macd(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS_macs_macd(port,tos)
																	
					
				elif var1==1 and var3==1:
		
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS_macs_ips(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS_macs_ips(port,tos)	
				
					for p in ports_switch:
						porta=p	
							
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS_macs_ips(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS_macs_ips(port,tos)
									
				elif var2==1 and var4==1:
		
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS_macd_ipd(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS_macd_ipd(port,tos)	
				
					for p in ports_switch:
						porta=p		
										
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS_macd_ipd(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS_macd_ipd(port,tos)
											
				else:
					
					num_ruleS=num_ruleS+1
					print "Insert rules of matching switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",num_ruleS
					
					port=52
					tos=0x04
					self.matching_flag_rule_in_switchS(port,tos)					
					
					port=52
					tos=0
					self.matching_flag_rule_in_switchS(port,tos)
				
					for p in ports_switch:
						porta=p	
											
						port=porta
						tos=0x04
						self.matching_flag_rule_in_switchS(port,tos)
							
						port=porta
						tos=0
						self.matching_flag_rule_in_switchS(port,tos)
						
		
			if C_match_S==N:
			 C_match_S=0	
															
  def forwarding_lowp_T(self):
	  
	  
		localtime = time.asctime( time.localtime(time.time()) ) 
				       	  
		global flag_match_T
		global num_ruleT
		global C_match_T
		global ip_src, ip_dst, mac_src, mac_dst	
		global var1,var2,var3,var4 
	 		  
		if self.connection.dpid > 100:
			
			  	
			C_match_T=C_match_T+1
						
			msg = nx.nx_flow_mod_table_id()
			self.connection.send(msg)
			
			if C_match_T==1:
				if flag_match_T==0:		
					flag_match_T=1
						
										
			if flag_match_T==1:
									
						
				if var1==1 and var2==1 and var3==1 and var4==1:
					
							
					self.forwarding_rules_lowpriority_switchT()		
					
				elif var1==1 and var2==1:
						
					self.forwarding_rules_lowpriority_switchT()		
											
				elif var3==1 and var4==1:
		
					self.forwarding_rules_lowpriority_switchT()						
					
				elif var1==1 and var3==1:
		
							
					self.forwarding_rules_lowpriority_switchT()	
									
				elif var2==1 and var4==1:
					
											
					self.forwarding_rules_lowpriority_switchT()	
											
				else:
					
					num_ruleT=num_ruleT+1
					print "Insert rules matching switch T  : ",localtime," Switch :",self.connection.dpid,"Count : ",num_ruleT
					
					self.forwarding_rules_lowpriority_switchT()	
				
				
			if C_match_T==N:
				C_match_T=0	
												     
  def read_counter(self):
	  
	  
	#sends the requests to all the switches in the topology connected to the controller	
	if self.connection.dpid <=40: 
	
		global flag_read
		global C_read	
			
		localtime = time.asctime( time.localtime(time.time()) ) 		
		C_read=C_read+1
						
		if C_read==1: 
			if flag_read==0:		
				flag_read=1
			elif flag_read==1:		
				flag_read=0	
		
		if flag_read==1:
			if self.connection.dpid==1 :							
				for connection in core.openflow._connections.values():
					connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))				
		elif flag_read==0:
			print "Waiting for other seconds in order to read counter ... "	  
			
		if C_read==N:
			C_read=0	  	


#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring without filters	
  def func1(self,mac_address_D,ip_address_D,tos,nwtos):
	  		
		mac_D=mac_address_D
		ip_D=ip_address_D
		t=tos
		nt=nwtos
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)

#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring with filter on ips and ipd				
  def func1_ips_ipd(self,mac_address_D,ip_address_D,ips,ipd,tos,nwtos):
	  		
		mac_D=mac_address_D
		ip_D=ip_address_D		
		IP_s=ips
		IP_d=ipd
		t=tos
		nt=nwtos
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)
	  
#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring with filter on macs and macd
  def func1_macs_macd(self, mac_address_D, ip_address_D, macs,macd,tos,nwtos):
	  	  
		mac_D=mac_address_D
		ip_D=ip_address_D		
		MAC_s=macs
		MAC_d=macd
		t=tos
		nt=nwtos
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)

#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring with filter on ips and macs											
  def func1_ips_macs(self, mac_address_D, ip_address_D,ips,macs,tos,nwtos):
	  
	  
		mac_D=mac_address_D
		ip_D=ip_address_D		
		IP_s=ips
		MAC_s=macs
		t=tos
		nt=nwtos
		
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt ))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)

#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring with filter on ipd and macd									
  def func1_ipd_macd(self, mac_address_D, ip_address_D,ipd,macd,tos,nwtos):
	  	  
		mac_D=mac_address_D
		ip_D=ip_address_D		
		IP_d=ipd
		MAC_d=macd
		t=tos
		nt=nwtos
		
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)

#match the flag in the packet and set the number of port of switch in the TOS field.....monitoring with filter on ips and macs and ipd and macd
  def func1_ips_ipd_macs_macd(self, mac_address_D, ip_address_D,ips,ipd,macs,macd,tos,nwtos):
	  	  
		mac_D=mac_address_D
		ip_D=ip_address_D
		IP_s=ips		
		IP_d=ipd
		MAC_s=macs
		MAC_d=macd
		t=tos
		nt=nwtos
		
		msg = nx.nx_flow_mod()
		msg.table_id = 2
		msg.priority = 10
		msg.idle_timeout = of.OFP_FLOW_PERMANENT
		msg.hard_timeout = of.OFP_FLOW_PERMANENT
		msg.match.of_eth_type = pkt.ethernet.IP_TYPE
		msg.match.of_eth_dst = EthAddr(mac_D)
		msg.match.of_ip_proto = 17
		msg.match.of_ip_dst = IPAddr(ip_D)
		msg.match.of_ip_tos=t
		msg.actions.append(of.ofp_action_nw_tos(nw_tos= nt))
		msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 3))
		self.connection.send(msg)


#rules forwarding in switch S
  def ForwardingRule_SwitchS_macs_macd_ips_ipd(self,port,tos,outport):
	  
	  
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_eth_src = EthAddr(mac_src)
			msg.match.of_eth_dst = EthAddr(mac_dst)
			msg.match.of_ip_src = IPAddr(ip_src)
			msg.match.of_ip_dst = IPAddr(ip_dst)
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)
			
  def ForwardingRule_SwitchS_ips_ipd(self,port,tos,outport):
			
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_ip_src = IPAddr(ip_src)
			msg.match.of_ip_dst = IPAddr(ip_dst)
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)

  def ForwardingRule_SwitchS_macs_macd(self,port,tos,outport):
			
			
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_eth_src = EthAddr(mac_src)
			msg.match.of_eth_dst = EthAddr(mac_dst)
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)

  def ForwardingRule_SwitchS_macs_ips(self,port,tos,outport):
			
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_eth_src = EthAddr(mac_src)
			msg.match.of_ip_src = IPAddr(ip_src)
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)

  def ForwardingRule_SwitchS_macd_ipd(self,port,tos,outport):
			
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_eth_dst = EthAddr(mac_dst)
			msg.match.of_ip_dst = IPAddr(ip_dst)
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)
	  
  def ForwardingRule_SwitchS(self,port,tos,outport):
			
			t=tos
			p=port
			out=outport
			msg = nx.nx_flow_mod()
			msg.table_id = 3
			msg.priority = 10
			msg.idle_timeout = of.OFP_FLOW_PERMANENT
			msg.hard_timeout = of.OFP_FLOW_PERMANENT
			msg.match.of_eth_type = pkt.ethernet.IP_TYPE
			msg.match.of_ip_tos=p
			msg.actions.append(of.ofp_action_nw_tos(nw_tos=t))
			msg.actions.append(of.ofp_action_output(port = out))
			self.connection.send(msg)
 
 
#insert the rules with high priority to forward tha packet 									
  def forwarding_high_p(self):
	  
	  
	  
	if self.connection.dpid <=40 :  
	  	  
		localtime = time.asctime( time.localtime(time.time()) ) 		  	 
		global C_forward_hp
		global dict2
		global flag_forward_hp
		global ip_src, ip_dst, mac_src, mac_dst	
		global var1,var2,var3,var4
		
		C_forward_hp=C_forward_hp+1
		
		msg = nx.nx_flow_mod_table_id()
		self.connection.send(msg)
		
		if C_forward_hp==1:
			if flag_forward_hp==0:		
				flag_forward_hp=1
			
			
		if flag_forward_hp==1:
						
			if var1==1 and var2==1 and var3==1 and var4==1:
							
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp			
				dpid=self.connection.dpid		
				
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS_macs_macd_ips_ipd(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS_macs_macd_ips_ipd(port,tos,outport)
							
				for porta in dict2[dpid].keys():
																				
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS_macs_macd_ips_ipd(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS_macs_macd_ips_ipd(port,tos,outport)
														
			elif var1==1 and var2==1:
				
				
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp			
				dpid=self.connection.dpid		
									
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS_ips_ipd(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS_ips_ipd(port,tos,outport)
							
				for porta in dict2[dpid].keys():
					
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS_ips_ipd(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS_ips_ipd(port,tos,outport)
																										
			elif var3==1 and var4==1:
				
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp			
				dpid=self.connection.dpid
								
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS_macs_macd(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS_macs_macd(port,tos,outport)		
															
				for porta in dict2[dpid].keys():
					
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS_macs_macd(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS_macs_macd(port,tos,outport)
																		
			elif var1==1 and var3==1:
				
				
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp		
				dpid=self.connection.dpid
				
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS_macs_ips(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS_macs_ips(port,tos,outport)		
								
				for porta in dict2[dpid].keys():
					
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS_macs_ips(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS_macs_ips(port,tos,outport)
																							
			elif var2==1 and var4==1:
				
				
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp		
				dpid=self.connection.dpid
				
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS_macd_ipd(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS_macd_ipd(port,tos,outport)	
								
				for porta in dict2[dpid].keys():
					
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS_macd_ipd(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS_macd_ipd(port,tos,outport)												    
						
			else:
				
				print "Insert rules table 3 in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_hp			
				dpid=self.connection.dpid
				
				outport=52
				port=((16<<3)+4)
				tos=((0<<3)+4)					
				self.ForwardingRule_SwitchS(port,tos,outport)							
				
				outport=52
				port=((16<<3))
				tos=((0<<3))					
				self.ForwardingRule_SwitchS(port,tos,outport)				
								
				for porta in dict2[dpid].keys():
					
					outport=porta
					port=((porta<<3)+4)
					tos=((0<<3)+4)					
					self.ForwardingRule_SwitchS(port,tos,outport)							
					
					outport=porta
					port=((porta<<3))
					tos=((0<<3))					
					self.ForwardingRule_SwitchS(port,tos,outport)					
														
		if C_forward_hp==N:
			C_forward_hp=0		

#set the port number of a specific switch in a TOS field of the IP packet in order to count the packet in output from a specific port of a switch	   	  
  def set_port_in_TOS(self):
	  
	  
	if self.connection.dpid <= 40:  
	  
		localtime = time.asctime( time.localtime(time.time()) ) 		       
		     
		global C_set_port
		global flag_set_port		
		global Array
		global ip_src, ip_dst, mac_src, mac_dst	
		global var1,var2,var3,var4
		global AllShortPath	
			
		ports = []
		ports_switch=[]
		limit=65534 	
		for m in self.connection.features.ports:
			ports.append(m.port_no)
		for element in ports:		
			if element < limit:
				ports_switch.append(element)		
		max = ports_switch[0] 
		pos = 1 
		while pos < len(ports_switch) : 
			if ports_switch[pos] > max : 
				max = ports_switch[pos] 
			pos = pos + 1 
		ports_switch.remove(max)
	 
		C_set_port=C_set_port+1
				
		msg = nx.nx_flow_mod_table_id()
		self.connection.send(msg)
		
		if C_set_port==1:
			if flag_set_port==0:		
				flag_set_port=1
			
			
		if flag_set_port==1:
						
			if var1==1 and var2==1 and var3==1 and var4==1:
								
				print "Switch DPID:  ", self.connection.dpid,"AT :  ",localtime				
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1_ips_ipd_macs_macd(mac_d,ip_d,ip_src,ip_dst,mac_src,mac_dst,tos,nwtos)
				
				tos=0
				nwtos=((16<<3))
				self.func1_ips_ipd_macs_macd(mac_d,ip_d,ip_src,ip_dst,mac_src,mac_dst,tos,nwtos)	
				
				
				ShortPath=[]
				
				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:								  	  
						s1_in=0
						s1_out=0
						ip_destination=0
						mac_destination=0												
						pos=0	
						
												
						if len(s)>1:																																		
																							
							s1_in=52
																																
							for r3 in Array:										
								if s[pos]==r3[0] and s[pos+1]==r3[1]:						
									s1_out=r3[2]																						
																					
							ip_destination="10.0.0."+str(s[len(s)-1])						
							mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)	
																																																										
							tos=0x04
							nwtos=((s1_out<<3)+4)											
							self.func1_ips_ipd_macs_macd(mac_destination,ip_destination,ip_src,ip_dst,mac_src,mac_dst,tos,nwtos)
							
							tos=0
							nwtos=((s1_out<<3))											
							self.func1_ips_ipd_macs_macd(mac_destination,ip_destination,ip_src,ip_dst,mac_src,mac_dst,tos,nwtos)
								
						
						
																																										 																																																																	
						elif len(s)==1:
							print" Shortest_Path with also one node "	
				
			elif var1==1 and var2==1:
				
				print "Switch DPID:  ", self.connection.dpid,"AT :  ",localtime				
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1_ips_ipd(mac_d,ip_d,ip_src,ip_dsttos,nwtos)
				
				tos=0
				nwtos=((16<<3))
				self.func1_ips_ipd(mac_d,ip_d,ip_src,ip_dst,tos,nwtos)
				
				
				ShortPath=[]
				
				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:
									  	  
						s1_in=0
						s1_out=0
						ip_destination=0
						mac_destination=0												
						pos=0							
						if len(s)>1:																																		
																								
							s1_in=52																									
							for r3 in Array:										
								if s[pos]==r3[0] and s[pos+1]==r3[1]:						
									s1_out=r3[2]																						
																					
							ip_destination="10.0.0."+str(s[len(s)-1])						
							mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)	
																																																										
							tos=0x04
							nwtos=((s1_out<<3)+4)																						
							self.func1_ips_ipd(mac_destination,ip_destination,ip_src,ip_dst,tos,nwtos)
							
							tos=0
							nwtos=((s1_out<<3))																						
							self.func1_ips_ipd(mac_destination,ip_destination,ip_src,ip_dst,tos,nwtos)
							
																																										 																																																																	
						elif len(s)==1:
							print" Shortest_Path with also one node "	
											
			elif var3==1 and var4==1:
				
				print "Switch DPID:  ", self.connection.dpid,"AT :  ",localtime				
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1_macs_macd(mac_d,ip_d, mac_src,mac_dst,tos,nwtos)
				
				tos=0
				nwtos=((16<<3))
				self.func1_macs_macd(mac_d,ip_d, mac_src,mac_dst,tos,nwtos)
				
				
				ShortPath=[]
				
				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:
									  	  
						s1_in=0
						s1_out=0
						ip_destination=0
						mac_destination=0												
						pos=0							
						if len(s)>1:																																		
																							
							s1_in=52																									
							for r3 in Array:										
								if s[pos]==r3[0] and s[pos+1]==r3[1]:						
									s1_out=r3[2]																						
																					
							ip_destination="10.0.0."+str(s[len(s)-1])						
							mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)	
																																																										
							tos=0x04
							nwtos=((s1_out<<3)+4)	
							self.func1_macs_macd(mac_destination,ip_destination,mac_src,mac_dst,tos,nwtos)
							
							tos=0
							nwtos=((s1_out<<3))	
							self.func1_macs_macd(mac_destination,ip_destination,mac_src,mac_dst,tos,nwtos)											
							
																																										 																																																																	
						elif len(s)==1:
							print" Shortest_Path with also one node "	
								
			elif var1==1 and var3==1:
				
				print "Switch DPID:  ", self.connection.dpid,"AT :  ",localtime				
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1_ips_macs(mac_d,ip_d,ip_src,mac_src,tos,nwtos)
				
				tos=0
				nwtos=((16<<3))
				self.func1_ips_macs(mac_d,ip_d,ip_src,mac_src,tos,nwtos)		
				
				
				ShortPath=[]
				
				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:
									  	  
						s1_in=0
						s1_out=0
						ip_destination=0
						mac_destination=0												
						pos=0							
						if len(s)>1:																																		
																							
							s1_in=52																									
							for r3 in Array:										
								if s[pos]==r3[0] and s[pos+1]==r3[1]:						
									s1_out=r3[2]																						
																					
							ip_destination="10.0.0."+str(s[len(s)-1])						
							mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)	
																																																										
							tos=0x04
							nwtos=((s1_out<<3)+4)
							self.func1_ips_macs(mac_destination, ip_destination, ip_src,mac_src,tos,nwtos)	
							
							tos=0
							nwtos=((s1_out<<3))
							self.func1_ips_macs(mac_destination, ip_destination, ip_src,mac_src,tos,nwtos)	
							
																																										 																																																																	
						elif len(s)==1:
							print" Shortest_Path with also one node "	
													
			elif var2==1 and var4==1:
				
				print "Switch DPID:  ", self.connection.dpid,"AT :  ",localtime				
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1_ipd_macd(mac_d,ip_d,ip_dst,mac_dst,tos,nwtos)
				
				
				tos=0
				nwtos=((16<<3))
				self.func1_ipd_macd(mac_d,ip_d,ip_dst,mac_dst,tos,nwtos)		
				
				
				ShortPath=[]
				
				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:
									  	  
						s1_in=0
						s1_out=0
						ip_destination=0
						mac_destination=0												
						pos=0							
						if len(s)>1:																																		
																							
							s1_in=52																									
							for r3 in Array:										
								if s[pos]==r3[0] and s[pos+1]==r3[1]:						
									s1_out=r3[2]																						
																					
							ip_destination="10.0.0."+str(s[len(s)-1])						
							mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)	
							
							
							tos=0x04
							nwtos=((s1_out<<3)+4)																																																			
							self.func1_ipd_macd(mac_destination,ip_destination,ip_dst,mac_dst,tos,nwtos)
														
							tos=0
							nwtos=((s1_out<<3))																																																			
							self.func1_ipd_macd(mac_destination,ip_destination,ip_dst,mac_dst,tos,nwtos)
							
																																										 																																																																	
						elif len(s)==1:
							print" Shortest_Path with also one node "				
						
			else:
				
				print "Insert rules of forwarding with priority equals to 10  start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_set_port		
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC			
				
				
				tos=0x04
				nwtos=((16<<3)+4)
				self.func1(mac_d,ip_d,tos,nwtos)
				
				
				tos=0
				nwtos=((16<<3))
				self.func1(mac_d,ip_d,tos,nwtos)

					
				
				ShortPath=[]				
				for S in AllShortPath:
					if S[0][0]==dpid:					
						ShortPath.append(S)
										
				for s in ShortPath[0]:
								  	  
					s1_in=0
					s1_out=0
					ip_destination=0
					mac_destination=0												
					pos=0	
											
					if len(s)>1:
																																																									
						s1_in=52																									
						for r3 in Array:										
							if s[pos]==r3[0] and s[pos+1]==r3[1]:						
								s1_out=r3[2]																						
																				
						ip_destination="10.0.0."+str(s[len(s)-1])						
						mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)																																																			
						
						
						tos=0x04
						nwtos=((s1_out<<3)+4)										
						self.func1(mac_destination,ip_destination,tos,nwtos)
						
						
						tos=0
						nwtos=((s1_out<<3))										
						self.func1(mac_destination,ip_destination,tos,nwtos)
						
																																																 																																																																	
					elif len(s)==1:
						print" Shortest_Path with also one node "						    
				
				
		if C_set_port==N:
			C_set_port=0		

#insert the rules with low priority to forward tha packet 			
  def forwarding_low_p(self):
	  
	if self.connection.dpid <= 40: 
	  
		localtime = time.asctime( time.localtime(time.time()) ) 
				       	 
		global C_forward_lp1, C_forward_lp2
		global flag_forward_lp1, flag_forward_lp2		
		global Array
		global Z
		global AllShortPath
				
		C_forward_lp1=C_forward_lp1+1
		
		
		msg = nx.nx_flow_mod_table_id()
		self.connection.send(msg)
		
		if C_forward_lp1==1:
			if flag_forward_lp1==0:		
				flag_forward_lp1=1	
			
		if flag_forward_lp1==1:
			
			C_forward_lp2=C_forward_lp2+1
			
			if C_forward_lp2==1:
				if flag_forward_lp2==0:
					flag_forward_lp2=1
					
					
			if flag_forward_lp2==1:
				
				print "Insert rules of forwarding in switch S start at  : ",localtime," Switch :",self.connection.dpid,"Count : ",C_forward_lp1
						
				dpid=self.connection.dpid
				
				val_mac=Z+dpid
				host_ip="10.0.0."
				host_mac="00:00:00:00:00:" 
				string_IP=str(host_ip)+str(dpid)
				ip_d=string_IP
				string_MAC=str(host_mac)+str(val_mac)
				mac_d=string_MAC				
																																				 									
				msg = nx.nx_flow_mod()
				msg.table_id = 0
				msg.priority = 1
				msg.idle_timeout = of.OFP_FLOW_PERMANENT
				msg.hard_timeout = of.OFP_FLOW_PERMANENT
				msg.match.of_eth_type = pkt.ethernet.IP_TYPE
				msg.match.of_eth_dst = EthAddr(mac_d)
				msg.match.of_ip_dst = IPAddr(ip_d)
				msg.actions.append(of.ofp_action_output(port = 52))
				self.connection.send(msg)
				
				spath_dpid="ShortPath"+str(dpid)
				spath_dpid=[]
				
				
				for node1 in G.nodes_iter():
					if node1 <=40:											
						shortest_path = NX.shortest_path(G,dpid,node1)
						spath_dpid.append(shortest_path)			
				
				AllShortPath.append(spath_dpid)			
					
				for s in spath_dpid:			  	  
					s1_in=0
					s1_out=0
					ip_destination=0
					mac_destination=0												
					pos=0	
											
					if len(s)>1:																																		
																						
						s1_in=52																									
						for r3 in Array:										
							if s[pos]==r3[0] and s[pos+1]==r3[1]:						
								s1_out=r3[2]																					
															
						ip_destination="10.0.0."+str(s[len(s)-1])						
						mac_destination="00:00:00:00:00:"+str(s[len(s)-1]+10)
																																																																																								 									
						msg = nx.nx_flow_mod()
						msg.table_id = 0
						msg.priority = 1
						msg.idle_timeout = of.OFP_FLOW_PERMANENT
						msg.hard_timeout = of.OFP_FLOW_PERMANENT
						msg.match.of_eth_type = pkt.ethernet.IP_TYPE
						msg.match.of_eth_dst = EthAddr(mac_destination)
						msg.match.of_ip_dst = IPAddr(ip_destination)
						msg.actions.append(of.ofp_action_output(port = s1_out))
						self.connection.send(msg)
																																																	
					elif len(s)==1:
						print" Shortest_Path with also one node "	
														 
			if C_forward_lp2==N:
					C_forward_lp2=0
				
				
		if C_forward_lp1==N:
			C_forward_lp1=0		

#get a label of a specific node in the given topology			
  def get_labels_nodes(self):
	  	  
	if self.connection.dpid <= 40:   
	  
		global C_get_labels
		global Array_Country
		global dict1
			
		C_get_labels=C_get_labels+1
		
		if C_get_labels==1:
			
			g = NX.read_graphml('Geant2012.graphml',str)
			
			for switch in g.nodes_iter(data = True):
				index=int(int(switch[0])+1)
				Array_Country[index]=switch[1]['label']	
				dict1[index] =switch[1]['label']
			print "Dizionario1 : ",dict1	
		if C_get_labels==N:
			C_get_labels=0				

		  										
def create_actions_list(actions):
        
        actionlist = []
        for action in actions:
            string = action.__class__.__name__ + "["
            string += action.show().strip("\n").replace("\n", ", ") + "]"
            actionlist.append(string)
        return actionlist																

#get statistics of all switches with the filter of flag set to 1
def print_statistics_flag1(event):
	
	
	if event.connection.dpid <=40:
	
		localtime = time.asctime( time.localtime(time.time()) )		
												
		n_packets_OUT_PORT52_1=0
		n_packets_IN_PORT52_1=0	
		counts_ports_in_1=[0]*20
		counts_ports_out_1=[0]*20
				
		for n in event.stats:
			
				
			if n.table_id ==3  and n.priority==10 and n.match.nw_tos==132:											
				n_packets_OUT_PORT52_1=n.packet_count
				
				
			elif n.table_id ==3  and n.priority==10 and n.match.nw_tos!=132 and  n.match.nw_tos!=128:									
				port_output=n.match.nw_tos
				if (port_output%8)==4:
					ris=(port_output-4)/8
					counts_ports_out_1[ris]=n.packet_count
								
				
			elif n.table_id ==0 and n.priority==10 and n.match.in_port==52 and n.match.nw_tos==0x04:			
				n_packets_IN_PORT52_1=n.packet_count
				
				
			elif n.table_id ==0 and n.priority==10 and n.match.in_port!=52 and n.match.nw_tos==0x04:			
				print "FLOWRULE: In_Port:",n.match.in_port,"IP_SRC",n.match.nw_src,"IP_DST",n.match.nw_dst,"DL_SRC",n.match.dl_src,"DL_DST",n.match.dl_dst,"NW_TOS:",n.match.nw_tos," Packet count: ", n.packet_count	
				port_input=n.match.in_port
				counts_ports_in_1[port_input]=n.packet_count
		
	
		
		return n_packets_OUT_PORT52_1,n_packets_IN_PORT52_1,counts_ports_out_1,counts_ports_in_1

#get statistics of all switches with the filter of flag set to 0			
def print_statistics_flag0(event):
	
	
	if event.connection.dpid <=40:
	
		localtime = time.asctime( time.localtime(time.time()) )		
									
		n_packets_OUT_PORT52_0=0
		n_packets_IN_PORT52_0=0	
		counts_ports_in_0=[0]*20
		counts_ports_out_0=[0]*20
		
		for n in event.stats:
							
	
			if n.table_id ==3  and n.priority==10 and n.match.nw_tos==128:											
				n_packets_OUT_PORT52_0=n.packet_count	
											
			elif n.table_id ==3  and n.priority==10 and n.match.nw_tos!=128 and n.match.nw_tos!=132 :											
				port_output=n.match.nw_tos
				if (port_output%8)==0:
					ris=port_output/8			
					counts_ports_out_0[ris]=n.packet_count
																												   
			elif n.table_id ==0 and n.priority==10 and n.match.in_port==52 and n.match.nw_tos==0:																								   						
				n_packets_IN_PORT52_0=n.packet_count
				
				
			elif n.table_id ==0 and n.priority==10 and  n.match.in_port!=52 and n.match.nw_tos==0:							
				print "FLOWRULE: In_Port:",n.match.in_port,"IP_SRC",n.match.nw_src,"IP_DST",n.match.nw_dst,"DL_SRC",n.match.dl_src,"DL_DST",n.match.dl_dst,"NW_TOS:",n.match.nw_tos," Packet count: ", n.packet_count
				port_input=n.match.in_port
				counts_ports_in_0[port_input]=n.packet_count
				
																			   								
		
		return n_packets_OUT_PORT52_0,n_packets_IN_PORT52_0,counts_ports_out_0,counts_ports_in_0						
 
#read the counters given from the flow statistics           
def create_flow_stats_list(event):
	
	global old
	
	if event.connection.dpid <=40 and event.connection.dpid!= old :
	
		old=event.connection.dpid
		
		global C_flow_stats, C_flow_stats_1
		global flag_flow_stats
		global VAR	
		
		global Count_in1_PORT52
		global Count_out1_PORT52	
		global Count_in0_PORT52
		global Count_out0_PORT52
			
		global sum_output1_port52, sum_input1_port52, sum_output0_port52, sum_input0_port52	
		
		global Count_in1_PORTS
		global Count_out1_PORTS	
		global Count_in0_PORTS
		global Count_out0_PORTS
		
		global somma_parziale_IN_0
		global somma_parziale_OUT_0
		
		global somma_parziale_IN_1
		global somma_parziale_OUT_1
		
		global Array_Country
		global dict1
		global dict2		
		global Results
		
		global port52
		global bit_value0
		global bit_value1	
		global direct1
		global direct2
		global periodDiz
		global period
		global cont1,cont2
		
		localtime = time.asctime( time.localtime(time.time()) )
		
		finaloutput0_1=[0]*20
		finalinput0_0=[0]*20
		finaloutput0_0=[0]*20
		finalinput0_1=[0]*20
		
		C_flow_stats=C_flow_stats+1
		
		if C_flow_stats==1:
									
			if VAR==1:		
				VAR=0
			elif VAR==0:		
				VAR=1
			
		if VAR==0:
			
			C_flow_stats_1=C_flow_stats_1+1
			
			if C_flow_stats_1==1:
							
				if flag_flow_stats==0:
					flag_flow_stats=1
				elif flag_flow_stats==1:
					flag_flow_stats=0	
				
				periodDiz=periodDiz+1					
				
			if flag_flow_stats==1:
				
				cont2=cont2+1
				
				item={}
				print "Read of counters with flag to 0"," Switch :",event.connection.dpid,"  start at : ",localtime
				
				item['Bit_value']=bit_value0
				item['Period']=periodDiz
											
				dpid=event.connection.dpid				
				item['SourceNode']=Array_Country[dpid]
				
				a,b,c,d=print_statistics_flag0(event)
								
				
				finaloutput0=a-Count_out0_PORT52[dpid]
				
				item['Port']=port52
				item['DestinationNode']=Array_Country[dpid]	
				item['Direction']=direct1
				item['Count']=finaloutput0
				Results.append(item)
				item={}
				
				finalinput0=b-Count_in0_PORT52[dpid]
				
				item['Bit_value']=bit_value0
				item['Period']=periodDiz
				item['SourceNode']=Array_Country[dpid]
				item['Port']=port52
				item['DestinationNode']=Array_Country[dpid]
				item['Direction']=direct2	
				item['Count']=finalinput0
				Results.append(item)
				
												
				Count_out0_PORT52[dpid]=a
				Count_in0_PORT52[dpid]=b
				
				sum_output0_port52=sum_output0_port52+finaloutput0
				sum_input0_port52=sum_input0_port52+finalinput0	
				
				
				
				for index, elem in enumerate(c):	
					if elem!=0:
						item={}
						item['Bit_value']=bit_value0
						item['Period']=periodDiz
						item['SourceNode']=Array_Country[dpid]
						print "Elem: ",elem
						print "Porta : ",index
						porta1=index
						print "c[porta1] : ",c[porta1]	
						item['Port']=porta1
						item['DestinationNode']=dict1[dict2[dpid][porta1]]	
						item['Direction']=direct1										
						finaloutput0_0[porta1]=c[porta1]-Count_out0_PORTS[(dpid*41)+porta1]						
						item['Count']=finaloutput0_0[porta1]						
						Count_out0_PORTS[(dpid*41)+porta1]=c[porta1]						
						Results.append(item)
														
						
				for index, element in enumerate(d):	
					if element!=0:
						item={}
						item['Bit_value']=bit_value0
						item['Period']=periodDiz
						item['SourceNode']=Array_Country[dpid]
						print "ELEM : : ",element
						print "Porta : ",index					
						porta=index
						print "d[porta] : ",d[porta]		
						item['Port']=porta	
						item['DestinationNode']=dict1[dict2[dpid][porta]]		
						item['Direction']=direct2										
						finalinput0_0[porta]=d[porta]-Count_in0_PORTS[(dpid*41)+porta]							
						item['Count']=finalinput0_0[porta]	
						Count_in0_PORTS[(dpid*41)+porta]=d[porta]
						Results.append(item)
						
						
				if cont2==N:
																			 					
					cont2=0																
				
				
			
			
			elif flag_flow_stats==0:
				
				
				cont1=cont1+1
				
				item={}
				print "Read of counters with flag to 1"," Switch :",event.connection.dpid," start at : ",localtime
				item['Bit_value']=bit_value1
				item['Period']=periodDiz	
										
				dpid=event.connection.dpid
				item['SourceNode']=Array_Country[dpid]
				
				a,b,c,d=print_statistics_flag1(event)
				
				
				finaloutput1=a-Count_out1_PORT52[dpid]
				
				item['Port']=port52
				item['DestinationNode']=Array_Country[dpid]	
				item['Direction']=direct1
				item['Count']=finaloutput1
				Results.append(item)
				item={}	
						
				finalinput1=b-Count_in1_PORT52[dpid]
				
				item['Bit_value']=bit_value1
				item['Period']=periodDiz
				item['SourceNode']=Array_Country[dpid]
				item['Port']=port52
				item['DestinationNode']=Array_Country[dpid]
				item['Direction']=direct2	
				item['Count']=finalinput1
				Results.append(item)
				
							
				Count_out1_PORT52[dpid]=a
				Count_in1_PORT52[dpid]=b
				
				sum_output1_port52=sum_output1_port52+finaloutput1
				sum_input1_port52=sum_input1_port52+finalinput1	
				
				for index, elem in enumerate(c):	
					if elem!=0:
						item={}
						item['Bit_value']=bit_value1
						item['Period']=periodDiz
						item['SourceNode']=Array_Country[dpid]
						print "ELEM : ",elem
						print "Porta : ",index
						porta2=index
						item['Port']=porta2	
						item['DestinationNode']=dict1[dict2[dpid][porta2]]	
						item['Direction']=direct1																
						finaloutput0_1[porta2]=c[porta2]-Count_out1_PORTS[(dpid*41)+porta2]						
						item['Count']=finaloutput0_1[porta2]
						Count_out1_PORTS[(dpid*41)+porta2]=c[porta2]
						Results.append(item)								
								
				for index, element in enumerate(d):	
					if element!=0:
						item={}
						item['Bit_value']=bit_value1
						item['Period']=periodDiz
						item['SourceNode']=Array_Country[dpid]
						print "ELEM : ",element
						print "Porta : ",index	
						porta3=index
						print "d[porta3] : ",d[porta3]
						item['Port']=porta3
						item['DestinationNode']=dict1[dict2[dpid][porta3]]	
						item['Direction']=direct2			
						finalinput0_1[porta3]=d[porta3]-Count_in1_PORTS[(dpid*41)+porta3]
						item['Count']=finalinput0_1[porta3]		
						Count_in1_PORTS[(dpid*41)+porta3]=d[porta3]
						Results.append(item)
						
				
				if cont1==N:
					
					cont1=0	
																							
							
											
			if C_flow_stats_1==N:
				C_flow_stats_1=0
											
		if VAR==1:
			
			print "Switch ", event.connection.dpid,"Waiting at ",localtime			
				
		if C_flow_stats==N:
			
			for pid in range(0,41):
				print "DPID : ",pid,"Count input 1 : ",Count_in1_PORTS[(pid*41)+1],"",Count_in1_PORTS[(pid*41)+2],"",Count_in1_PORTS[(pid*41)+3],Count_in1_PORTS[(pid*41)+4],Count_in1_PORTS[(pid*41)+5],Count_in1_PORTS[(pid*41)+6],Count_in1_PORTS[(pid*41)+7],Count_in1_PORTS[(pid*41)+8],Count_in1_PORTS[(pid*41)+9],Count_in1_PORTS[(pid*41)+10]
				
			for pid in range(0,41):
				print "DPID : ",pid,"Count output 1: ",Count_out1_PORTS[(pid*41)+1],"",Count_out1_PORTS[(pid*41)+2],"",Count_out1_PORTS[(pid*41)+3],Count_out1_PORTS[(pid*41)+4],Count_out1_PORTS[(pid*41)+5],Count_out1_PORTS[(pid*41)+6],Count_out1_PORTS[(pid*41)+7],Count_out1_PORTS[(pid*41)+8],Count_out1_PORTS[(pid*41)+9],Count_out1_PORTS[(pid*41)+10]
				
			for pid in range(0,41):
				print "DPID : ",pid,"Count input 0: ",Count_in0_PORTS[(pid*41)+1],"",Count_in0_PORTS[(pid*41)+2],"",Count_in0_PORTS[(pid*41)+3],Count_in0_PORTS[(pid*41)+4],Count_in0_PORTS[(pid*41)+5],Count_in0_PORTS[(pid*41)+6],Count_in0_PORTS[(pid*41)+7],Count_in0_PORTS[(pid*41)+8],Count_in0_PORTS[(pid*41)+9],Count_in0_PORTS[(pid*41)+10]
				
			for pid in range(0,41):
				print "DPID : ",pid,"Count output 0: ",Count_out0_PORTS[(pid*41)+1],"",Count_out0_PORTS[(pid*41)+2],"",Count_out0_PORTS[(pid*41)+3],Count_out0_PORTS[(pid*41)+4],Count_out0_PORTS[(pid*41)+5],Count_out0_PORTS[(pid*41)+6],Count_out0_PORTS[(pid*41)+7],Count_out0_PORTS[(pid*41)+8],Count_out0_PORTS[(pid*41)+9],Count_out0_PORTS[(pid*41)+10]				
				
			for pid in range(0,41):
				print "DPID : ",pid,"Count out 0 porta 52",Count_out0_PORT52[pid]
			for pid in range(0,41):
				print "DPID : ",pid,"Count in 0 porta 52",Count_in0_PORT52[pid]
			for pid in range(0,41):
				print "DPID : ",pid,"Count out 1 porta 52",Count_out1_PORT52[pid]
			for pid in range(0,41):
				print "DPID : ",pid,"Count in 1 porta 52 ",Count_in1_PORT52[pid]
							
					
			print "The sum of all counters in output in the port 52 with flag 1 : ",sum_output1_port52			
			print "The sum of all counters in input in the port 52 with flag  1 : ",sum_input1_port52			
			print "The sum af all counters in output in the port 52 with flag 0 : ",sum_output0_port52		
			print "The sum of all counters in input in the port 52 with flag  0 : ",sum_input0_port52		
			print "Iterazione : ",periodDiz
					
			sum_output1_port52=0
			sum_input1_port52=0
			sum_output0_port52=0
			sum_input0_port52=0
			
			
			C_flow_stats=0

	
def is_valid_ipv4_address(address):
			    try:
			        socket.inet_pton(socket.AF_INET, address)
			    except AttributeError:  # no inet_pton here, sorry
			        try:
			            socket.inet_aton(address)
			        except socket.error:
			            return False
			        return address.count('.') == 3
			    except socket.error:  # not a valid address
			        return False
			
			    return True

def is_valid_mac_address(address):
	
    if address.count(":")!=5:
        return False
    for i in address.split(":"):
        for j in i:
            if j>"F" or (j<"A" and not j.isdigit()) or len(i)!=2:
                return False
    return True 			    
			    							
class l2_learning (object):
	
  global G
 
  
  def __init__ (self,transparent):	  		
	
	global run_once 
	global c1
	global ip_src, ip_dst, mac_src, mac_dst
	global var1,var2,var3,var4
	iplist=[] 
	
	          	 	  	  	          
	if run_once == 0:
				
		import re	
			
		while len(iplist)<4:												 
			ip_list = raw_input('<usage>:[<IP_SRC>] [<IP_DST>] [<MAC_SRC>] [<MAC_DST>]:')
			iplist=ip_list.split(" ")	
					
		if len(iplist)==4:			
			if iplist[0]=="null" and iplist[1]=="null" and iplist[2]=="null" and iplist[2]=="null":				
				print "Monitoring all traffic without filters"
			else:					
				while ((is_valid_ipv4_address(iplist[0])==False and iplist[0]!="null") or (is_valid_ipv4_address(iplist[1])==False and iplist[1]!="null") or (is_valid_mac_address(iplist[2])==False   and iplist[2]!="null") or (is_valid_mac_address(iplist[3])==False  and iplist[3]!="null")):				
					ip_list = raw_input('<usage>:[<IP_SRC>] [<IP_DST>] [<MAC_SRC>] [<MAC_DST>]:')
					iplist=ip_list.split(" ")
					
		if len(iplist)==1:
			ip_src=iplist[0]			
		elif len(iplist)==2:
			ip_src=iplist[0]
			ip_dst=iplist[1]
		elif len(iplist)==3:
			ip_src=iplist[0]
			ip_dst=iplist[1]
			mac_src=iplist[2]
		elif len(iplist)==4:
			ip_src=iplist[0]
			ip_dst=iplist[1]
			mac_src=iplist[2]
			mac_dst=iplist[3]
										
		if ip_src!="null":
			print"Monitoring IP_SRC:",ip_src
			var1=1
		if ip_dst!="null":
			print"Monitoring IP_DST:",ip_dst
			var2=1
		if mac_src!="null":
			print"Monitoring MAC_SRC:",mac_src
			var3=1
		if mac_dst!="null":
			print"Monitoring MAC_DST:",mac_dst
			var4=1				
											
		run_once = 1 
	
	
	def startup():
				
            core.openflow.addListeners(self, priority = 0)
            core.openflow_discovery.addListeners(self)
            self.transparent = transparent
	
	core.call_when_ready(startup, ('openflow','openflow_discovery'))
	
 
  def _handle_LinkEvent(self, event):  
	  
	global Array
	global M
	global C_link_event
	global dict2
			
	l = event.link
	
	sw1 = l.dpid1
	sw2 = l.dpid2
	pt1 = l.port1
	pt2 = l.port2
	
	G.add_node( sw1 )
	G.add_node( sw2 )
	
	if event.added:		
		G.add_edge(sw1,sw2)
	if event.removed:
		try:
			G.remove_edge(sw1,sw2)
		except:			
			print "Remove edge "
			
	C_link_event=C_link_event+1		
	print "Counter : ",C_link_event,"sw1 : ",l.dpid1,"sw2 :",l.dpid2,"Port1: ",pt1,"Port2 : ",pt2
			
	array=[]
	if sw1 <=40 and sw2 <=40:
					
		array.insert(0,sw1)
		array.insert(1,sw2)
		array.insert(2,pt1)
		array.insert(3,pt2)	
		
		Array.append(array)	
		
		if sw1 not in dict2:		
			dict2[sw1] = {}
		dict2[sw1][pt1]=sw2
			
		if sw2 not in dict2:
			dict2[sw2] = {}
		dict2[sw2][pt2]=sw1
		
	if C_link_event==M:
			
		print "Fine Link detection..."	
		print "Dizionario2 :",dict2	
		       
  def _handle_ConnectionUp (self, event):
	 
	LearningSwitch(event.connection, self.transparent)
		
def signal_handler(signal,frame):
	  
		global Results		
		print "Results: ",Results,"LEN : ",len(Results)	
	    
		with open('/home/fmesolella/Desktop/results.json', 'w') as outfile:
					json.dump(Results, outfile, indent=4) 
					
		sys.exit(0)
			
def launch (transparent=False, hold_down=_flood_delay):
 
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")
  def start ():
    if not core.NX.convert_packet_in:
      log.error("PacketIn conversion required")
      return
    log.info("Simple NX switch running.")
  core.call_when_ready(start, ['NX','openflow']) 
  
  core.registerNew(l2_learning, str_to_bool(transparent)) 
  
  signal.signal(signal.SIGINT, signal_handler)

 

 
