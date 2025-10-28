#An NLP library for Timeline Extraction. 

##Installation

`pip install pytlex`

##Get started

###How to create a TimeML Graph
####From a TimeML File(must provide a valid TimeML file):

`timeML_graph = Graph('wsj_0555.tml')` 

####Using TimeML text (must be in the correct TimeML format):

```
timeML_graph = Graph("<TimeML
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="../../dtd/timeml_1.2.1.xsd">
    </TimeML>")
```
    
 
####Using the graph definition (a set of nodes and links):

```
node1 = TimeX(50, "FUTURE_REF", True, "next wednesday")
node2 = TimeX(51, "FUTURE_REF", True, "next thursday")
node3 = TimeX(52, "FUTURE_REF", True, "next friday")
link1 = Link(50, "TLINK", "BEFORE", node1, node2)
link2 = Link(51, "TLINK", "BEFORE", node2, node3)
timeML_nodes = set()
timeML_nodes.add(node1)
timeML_nodes.add(node2)
timeML_nodes.add(node3)
timeML_links.add(link1)
timeML_links.add(link2)
timeML_graph = Graph(timeML_nodes, timeML_links)
```


####Accessing a graph's partitions (main and subordination partitions):

```
timeML_graph = Graph('wsj_0555.tml')
timeML_graph.main_partitions
timeML_graph.subordination_parittions
```

####Accessing a graph's timeline:
```
timeML_graph = Graph('wsj_0555.tml')
timeML_graph.timeline
```




