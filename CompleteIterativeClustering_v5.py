# Updated 14-Mar-2018 14:27
import sys
import json
import random
import networkx as nx
import time

def clustering(edges,n):
    # complexity m+ m * (sum_(i from 1 to m) m-i) = m+ (m* (m-1)/2) = O(m^2)
    # in the worst case (when every cluster has only one link)

    Atilde=[[] for x in range(n)]

    #O(m)
    for edge in edges:
        Atilde[edge[0]].append(edge)

    for i in range(n):
        if len(Atilde[i])>0:

            for Atilde_j in Atilde[i]:

                sec=Atilde_j[1]

                for ii in range(i+1,len(Atilde)):
                    if len(Atilde[ii])>0:
                        for Atilde_jj in Atilde[ii]:

                            if Atilde_jj[1]==sec:
                                Atilde[i].extend(Atilde[ii])
                                Atilde[ii]=[]
                                break
    # Remove empty clusters
    Atilde=filter(None, Atilde)
    return Atilde

def my_has_path(G, source, target):

    try:
        sp = nx.shortest_path(G, source, target)
    except nx.NetworkXNoPath:
        return []
    return sp

def myeccentricity(G, v=None, sp=None):

    order=G.order()

    e={}
    for n in G.nbunch_iter(v):
        if sp is None:
            length=nx.single_source_shortest_path_length(G,n)
            L = len(length)
        else:
            try:
                length=sp[n]
                L = len(length)
            except TypeError:
                raise nx.NetworkXError('Format of "sp" is invalid.')

        e[n]=max(length.values())

    if v in G:
        return e[v]
    else:
        return e

def mydiameter(G, e=None):

    if e is None:
        e=myeccentricity(G)
    return max(e.values())


if __name__ == "__main__":

    # Sanity check
    if len(sys.argv)!=3:
        sys.stderr.write("usage: %s graphml_file [sampling_rate] [monitored nodes list]\n"%sys.argv[0])
        exit()

    try:
        # Rate
        rate=int(sys.argv[2])

        if rate<0 or rate>100:
            sys.stderr.write("Sampling rate must be [0,100]\n")
            exit()

    except ValueError:
        # List of monitored nodes
        rate=-1
        try:
            input_list=json.loads(sys.argv[2])
        except ValueError:
            sys.stderr.write("Wrong list format")
            exit()

    # Import graph
    graph=nx.read_graphml(sys.argv[1],str)

    print("Graph %s has %d physical nodes with %d physical edges"
          % (graph.name, nx.number_of_nodes(graph), nx.number_of_edges(graph)))

    n_nodes=nx.number_of_nodes(graph)
    n_edges=nx.number_of_edges(graph)

    # Adapt to networkx version
    if float(nx.__version__)>=2.0:
        edges_iter=graph.edges
        nodes_iter=graph.nodes
    else:
        edges_iter=graph.edges_iter
        nodes_iter=graph.nodes_iter

    # Node labels
    geolabels=['' for i in range(n_nodes)]
    for node in nodes_iter(data=True):
        geolabels[int(node[0])]=node[1]['label']

    # Setup input and output interfaces
    # Setup external links
    in_interfaces={}
    out_interfaces={}
    Enodes=[]
    Eedges=[]
    n=0

    for edge in edges_iter(data=True):
        x=int(edge[0])
        y=int(edge[1])

        if x not in out_interfaces:
            out_interfaces[x]={}
        if y not in out_interfaces:
            out_interfaces[y]={}
        if x not in in_interfaces:
            in_interfaces[x]={}
        if y not in in_interfaces:
            in_interfaces[y]={}

        n0=(n,x,y,"out")
        n1=(n+1,y,x,"out")
        n2=(n+2,x,y,"in")
        n3=(n+3,y,x,"in")
        out_interfaces[x][y]=n0
        out_interfaces[y][x]=n1
        in_interfaces[x][y]=n2
        in_interfaces[y][x]=n3
        Enodes.extend([n0,n1,n2,n3])
        Eedges.extend([(n0,n3),(n1,n2)])
        n+=4

    # Setup internal links
    for node in in_interfaces:
        for intf1 in in_interfaces[node]:
            in_intf=in_interfaces[node][intf1]
            for intf2 in out_interfaces[node]:
                out_intf=out_interfaces[node][intf2]
                Eedges.append((in_intf,out_intf))

    # Extended graph
    extended_graph=nx.DiGraph()
    extended_graph.add_nodes_from(Enodes)
    extended_graph.add_edges_from(Eedges)

    print ("Extended graph: %d nodes, %d edges" %(len(Enodes),len(Eedges)))

    # Set seed for reproducibility
    #random.seed(0)

    if (rate>=0):
        Mnodes = random.sample(Enodes,((len(Enodes)*rate)/100))
    else:
        Mnodes = []
        for e in Enodes:
            for i in input_list:
                if i[0]==e[1] and i[1]==e[2] and i[2]==e[3]:
                    Mnodes.append(e)

    #print "Mnodes",Mnodes

    # Monitored graph
    monitored_graph=nx.DiGraph()
    monitored_graph.add_nodes_from(Mnodes)

    find_monitored_edges_start = time.time()
    # Save all the links in the extended graph
    # with a monitored node as one extremity
    links_to_mnodes={}

    for edge in extended_graph.edges():
    #for edge in extended_graph.edges_iter(): # nx version < 2.0
        if edge[0] in Mnodes: 

            if edge[0] not in links_to_mnodes:
                links_to_mnodes[edge[0]]={"in":[],"out":[]}

            links_to_mnodes[edge[0]]["out"].append(edge)

        if edge[1] in Mnodes:

            if edge[1] not in links_to_mnodes:
                links_to_mnodes[edge[1]]={"in":[],"out":[]}

            links_to_mnodes[edge[1]]["in"].append(edge)

    # Remove from the Extended graph all to monitored nodes
    extended_graph.remove_nodes_from(Mnodes)

    # Add edges to the monitored graph
    MEdges_to_EPath={}
    for n in monitored_graph.nodes():
        for d in monitored_graph.nodes():

            if(n!=d):

                # Add the 2 monitored nodes to the pruned extended graph
                extended_graph.add_node(n)
                extended_graph.add_node(d)

                for link in links_to_mnodes[n]["in"]:
                    if link[0] not in Mnodes or link[0]==d:
                        extended_graph.add_edge(link[0],link[1])

                for link in links_to_mnodes[n]["out"]:
                    if link[1] not in Mnodes or link[1]==d:
                        extended_graph.add_edge(link[0],link[1])

                for link in links_to_mnodes[d]["in"]:
                    if link[0] not in Mnodes or link[0]==n:
                        extended_graph.add_edge(link[0],link[1])

                for link in links_to_mnodes[d]["out"]:
                    if link[1] not in Mnodes or link[1]==n:
                        extended_graph.add_edge(link[0],link[1])

                path= my_has_path(extended_graph,n,d)

                if (len(path)>0):

                    monitored_graph.add_edge(n,d)
                    MEdges_to_EPath[(n[0],d[0])]=path

                extended_graph.remove_node(n)
                extended_graph.remove_node(d)

    find_monitored_edges_time = time.time() - find_monitored_edges_start
    print "Time to find edges in the monitored network: "+str(find_monitored_edges_time)+" sec."

    print ("Monitored graph: %d nodes, %d edges"
          %(len(monitored_graph.nodes()),len(monitored_graph.edges())))
    
    # Extended graph node index -> Monitored graph node with incremental index
    # (because the clustering algorithm needs an incremental node)
    extended_to_monitored={}
    monitored_to_extended={}
    i=0
    for old_node in Mnodes:
        extended_to_monitored[old_node[0]]=i
        monitored_to_extended[i]=old_node
        i+=1

    incremental_edges=[]
    for edge in monitored_graph.edges():
        incremental_edges.append((extended_to_monitored[edge[0][0]],extended_to_monitored[edge[1][0]]))

    # Clustering
    clustering_start = time.time()
    clusters=clustering(incremental_edges,len(monitored_graph.nodes()))
    clustering_time = time.time()-clustering_start
    print "Clustering time: "+str(clustering_time)+" sec."

    # Dump clusters
    dump=[]

    for cl in clusters:
        labeled_cl=[]
        raw_cl=[]
        for edge in cl:
            src=monitored_to_extended[edge[0]]
            dst=monitored_to_extended[edge[1]]

            src_label="%s-%s-%s"%(geolabels[src[1]],geolabels[src[2]],src[3])
            dst_label="%s-%s-%s"%(geolabels[dst[1]],geolabels[dst[2]],dst[3])
            labeled_cl.append("(%s,%s),"%(src_label,dst_label))
            raw_cl.append((src,dst))
        dump.append({"raw":raw_cl,"labeled":labeled_cl,"size":len(cl)})

    nx.write_graphml(monitored_graph, "Monitored.graphml")

    with open('clusters.json', 'w') as cfile:
        json.dump(dump, cfile, indent=4)

    print "Clusters: %d"%len(clusters)

    # Get Stats

    # Compute Diameter for Extended Graph and Monitored Graph

    cluster_id=0
    info_clusters=[]

    for clu in clusters:
        info_cluster={}
        #print "Cluster : ",clu,"Len : ",len(clu)
        info_cluster['id']=cluster_id
        Edges_cluster_ext=[]
        Edges_cluster=[]
        All_paths=[]

        for edg in clu:
            Edges_cluster.append(edg)

            src_idx=monitored_to_extended[edg[0]][0]
            dst_idx=monitored_to_extended[edg[1]][0]

            Edges_cluster_ext.append( (src_idx,dst_idx) )

            path = MEdges_to_EPath [ (src_idx,dst_idx) ]
            All_paths.append(path)

        # Build cluster extended graph
        cluster_extended_graph=nx.DiGraph()
        for path in All_paths:
            cluster_extended_graph.add_path(path)

        print ("Cluster in the Extended  Graph: %d nodes, %d edges"
          %(len(cluster_extended_graph.nodes()),len(cluster_extended_graph.edges())))

        info_cluster['num_extended_nodes']=len(cluster_extended_graph.nodes())
        info_cluster['num_extended_edges']=len(cluster_extended_graph.edges())

        diameter1  = mydiameter(cluster_extended_graph)
        print 'Diameter in the Extended Graph : ', diameter1
        info_cluster['extended_diameter']=diameter1

        # Build cluster monitored graph
        cluster_monitored_graph=nx.DiGraph()
        cluster_monitored_graph.add_edges_from(Edges_cluster)

        print ("Cluster in the Monitored Graph: %d nodes, %d edges"
          %(len(cluster_monitored_graph.nodes()),len(cluster_monitored_graph.edges())))

        info_cluster['num_monitored_nodes']=len(cluster_monitored_graph.nodes())
        info_cluster['num_monitored_edges']=len(cluster_monitored_graph.edges())

        diameter2  = mydiameter(cluster_monitored_graph)
        print 'Diameter in the Monitored Graph : ', diameter2
        info_cluster['monitored_diameter']=diameter2

        print "Dictionary of Cluster: ",info_cluster
        info_clusters.append(info_cluster)

        # DEBUG
        if len(cluster_extended_graph.nodes()) < len(cluster_monitored_graph.nodes()):
            sys.stderr.write("All_paths : %s\n\n"%All_paths)
            print "-------------------------ERRORRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR--------------------------"
            sys.stderr.write("Edge_cluster : %s\n\n"%Edges_cluster)
            sys.stderr.write("Monitored to EXt : %s\n\n"%monitored_to_extended)
            sys.stderr.write("Ext to Monit : %s\n\n"%extended_to_monitored)
            sys.stderr.write("-----EDges M: %s\n\n"%cluster_monitored_graph.edges())
            sys.stderr.write("-----EDges E: %s\n\n"%cluster_extended_graph.edges())


        cluster_id+=1


    #print "Informations about Clusters: ",info_clusters
    data=[]
    
      
    if type(sys.argv[2]) is int:{

        data.append({"topology":str(sys.argv[1]),"rate":int(sys.argv[2]),"num_clusters":len(clusters),"info_clusters":info_clusters,"Monitored_graph_nodes":len(monitored_graph.nodes()),"Monitored_graph_edges":len(monitored_graph.edges()),"Extended_graph_nodes":len(Enodes),"Extended_graph_edges":len(Eedges),"Monitored_edges_time":find_monitored_edges_time,"Clustering_time":clustering_time})
    }
    elif type(sys.argv[2]) is str: {
        data.append({"topology":str(sys.argv[1]),"nodes":str(sys.argv[2]),"num_clusters":len(clusters),"info_clusters":info_clusters,"Monitored_graph_nodes":len(monitored_graph.nodes()),"Monitored_graph_edges":len(monitored_graph.edges()),"Extended_graph_nodes":len(Enodes),"Extended_graph_edges":len(Eedges),"Monitored_edges_time":find_monitored_edges_time,"Clustering_time":clustering_time})

      }  

    with open('totclusters.json', 'w') as tcfile:
        json.dump(data, tcfile, indent=4)


   

   
