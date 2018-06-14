import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import json
import sys
import collections
from matplotlib.ticker import MultipleLocator

dictionary = plt.figure()
Link=[]
LostPacket=[]

D2={}
D3={}
D4={}
D5={}
D6={}
D7={}



Tot=[]
Tot1=[]

width = 0.9
input_file=open('results.json', 'r')
json_decode=json.load(input_file)


for item in json_decode:	
	if item['Direction']=="output" and item['SourceNode']!=item['DestinationNode']:	
		print "item",item	
		for it in json_decode:									
		  if it['Direction'] != item['Direction'] and it['SourceNode'] == item['DestinationNode'] and item['SourceNode'] == it['DestinationNode']:				  	 
			 if item['Period']==it['Period'] :
				 print(str(it['Period']) + ' ' + it['SourceNode'] + ' ' + it['DestinationNode'] + ' ' + it['Direction']+ ' ' + str(it['Count']))					 				 
				 lost_packet=item['Count']-it['Count']				 
				 if item['Count'] !=0:
					 Percent=(100*float(lost_packet))/float(item['Count'])
					 print "Percent : ",Percent
				 print str(it['Period'])+' '+"Lost : ",lost_packet			 
				 if it['Period']==2:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D2[link]=lost_packet
					Link.append(link)
					LostPacket.append(lost_packet)					
				 if it['Period']==3:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D3[link]=lost_packet					
					Link.append(link)
					LostPacket.append(lost_packet)						
				 elif it['Period']==4:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D4[link]=lost_packet
					Link.append(link)
					LostPacket.append(lost_packet)		
				 elif it['Period']==5:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D5[link]=lost_packet
					Link.append(link)
					LostPacket.append(lost_packet)					
				 elif it['Period']==6:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D6[link]=lost_packet
					Link.append(link)
					LostPacket.append(lost_packet)					
				 elif it['Period']==7:
					link=item['SourceNode']+':'+item['DestinationNode']
					print "Link",link
					D7[link]=lost_packet
					Link.append(link)
					LostPacket.append(lost_packet)					

od2 = collections.OrderedDict(sorted(D2.items()))
print "OD2--->",od2,"LEN : ",len(od2)
od3 = collections.OrderedDict(sorted(D3.items()))	
print "OD3--->",od3	,"LEN : ",len(od3)			
od4 = collections.OrderedDict(sorted(D4.items()))
print "OD4--->",od4,"LEN : ",len(od4)
od5 = collections.OrderedDict(sorted(D5.items()))
print "OD5-->",od5,"LEN : ",len(od5)
od6 = collections.OrderedDict(sorted(D6.items()))	
print "OD6--->",od6	,"LEN : ",len(od6)			
od7 = collections.OrderedDict(sorted(D7.items()))
print "OD7--->",od7,"LEN : ",len(od7)


print "LostPacket : ",LostPacket,len(LostPacket)
somma=0
for l in LostPacket:
	somma=somma+l
print "Totally Packet loss",somma


dataset1 = np.array(od2.values())
dataset2 = np.array(od3.values())
dataset3 = np.array(od4.values())
dataset4 = np.array(od5.values())
dataset5 = np.array(od6.values())
dataset6 = np.array(od7.values())

result=[]
for i in range(0, len(dataset2)):
   result.insert(i,(dataset1[i]+dataset2[i]+dataset3[i]+dataset4[i]+dataset5[i]+dataset6[i]))
   
									
p1=plt.bar(range(len(od2)), od2.values(),width, align='center')
p2=plt.bar(range(len(od3)), od3.values(),width,bottom=dataset1,align='center')
p3=plt.bar(range(len(od4)), od4.values(),width,bottom=dataset1+dataset2,align='center')
p4=plt.bar(range(len(od5)), od5.values(),width,bottom=dataset1+dataset2+dataset3,align='center')
p5=plt.bar(range(len(od6)), od6.values(),width,bottom=dataset1+dataset2+dataset3+dataset4,align='center')
p6=plt.bar(range(len(od7)), od7.values(),width,bottom=dataset1+dataset2+dataset3+dataset4+dataset5,align='center')


n=5
ha = ['right', 'center', 'left']

def after(value, a):
    # Find and validate first part.
    pos_a = value.rfind(a)
    if pos_a == -1: return ""
    # Returns chars after the found string.
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= len(value): return ""
    return value[adjusted_pos_a:]
    
Lab=[]

for x in od3.keys():
	y=(after(x, ":"))
	s=x[:5]+"-"+y[:5]
	Lab.append(s)

plt.xticks(range(len(od3)),Lab, fontsize=10,rotation=45,ha=ha[0])
plt.tight_layout()

plt.legend((p1[0],p2[0],p3[0],p4[0],p5[0],p6[0]), ('Period1','Period2', 'Period3','Period4','Period5','Period6'),fontsize=18)

plt.grid(axis="y")
plt.ylabel('Packet Loss',fontsize=18)
plt.xlabel('Link',fontsize=18)
#plt.xticks(rotation='vertical')
plt.title('Monitoring Packet Loss',fontsize=18)
plt.show()
