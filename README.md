# Multipoint-monitoring

This repository contains the code and instructions to reproduce the experiments presented in the paper:

```
Mauro Cociglio, Giuseppe Fioccola, Guido Marchetto, Amedeo Sapio, and Riccardo Sisto.
"Multipoint passive monitoring in packet networks"
```

## Clustering script
### Requirements
`pip install networkx`

### Execution

The 2 scripts `CompleteIterativeClustering_v5.py` and `CompleteRecursiveClustering_v1.py` perform the iterative clustering algorithm and recursive clustering algorithm, respectively.

Each clustering script takes as input:

- a topology file in the graphml format
- either a sampling ratio (percentage of nodes in the extended graph that are monitored, randomly selected) or a list of nodes that are monitored

and its output is:

- on the standard output, the dimensions and timing information on the computed graphs and clusters

- the `clusters.json` file containing the computed clusters. Each cluster is described as a list of edges (couple of nodes)
- the `totclusters.json` file containing a list of features (e.g., dimensions) of the monitored graph, extended graph and of every single cluster
- the `Monitored.graphml` file containing the monitored graph in the graphml format

### Example

This example runs the iterative clustering algorithm on the BICS topology. The algorithm first computes the extended graph and then selects 10% of all the nodes in the extended graph as monitored nodes.

`python CompleteIterativeClustering_v5.py topologies/Bics.graphml 10`

To explicitely select the nodes of the extended graph to monitor, we can provide a list of nodes instead of a sampling ratio:

`python CompleteIterativeClustering_v5.py topologies/Bics.graphml "[[3,20,\"in\"],[3,20,\"out\"],[3,14,\"in\"],[3,14,\"out\"]]"`

With this command we are selecting:

- the interface of node 3 that is connected to node 20 in the input direction
- the interface of node 3 that is connected to node 20 in the output direction
- the interface of node 3 that is connected to node 14 in the input direction
- the interface of node 3 that is connected to node 14 in the output direction

The node IDs are the ones defined in the topology graphml file:

- node 3 is the `Rotterdam` node
- node 20 is the `Amsterdam` node
- node 14 is the `Brussels` node

In the `clusters.json` file, a cluster is described in 2 formats. In the 'raw' format the edges are represented as 2 nodes, each in the format `(N, ID, rID, direction)` where:

- N is an incremental number assigned to all the nodes of the extended graph
- ID is the node ID in the topology graphml file
- rID is the node ID on the other end of the link
- direction is either 'in' or 'out'

In the 'labeled' format the IDs are replaced with the label of each node, taken from the topology graphml file. As an example, one edge can be the following:

`(Rotterdam-Amsterdam-in,Rotterdam-Amsterdam-out)`
