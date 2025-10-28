from pytlex_core.data import Graph, Link
from pytlex_core.algorithms import Connectivity_Increaser as ci

single_links = set()

"""
Main function of the Partitioner script. 
@:arg Graph, original TimeML Graph
@:returns dict, with the key, value pairs:
                "main_graphs" : [Graph]
                "subordination_graphs" : [Graph]
                "s_links": {Link}
        
"""


def partition_graph(original_graph: Graph):
    global single_links
    visited_nodes = set()
    sub_graph_list = []
    # create a copy of the graph to avoid modifying the original graph
    temp_graph_links = original_graph.links.copy()

    for link in temp_graph_links.values():
        """
        determine if any SLinks have a TLink going in the same or opposite directions
        if they do, then these links do not yield a new partition (this will be called redundancy)
        if they don't they will be called single_s_links and will be stored in a single_links set
        """
        if link.link_tag == 'SLINK':
            single_s_link = True
            """
            obtain all links related to a specific node, 
            with which we will determine the nodes related to the initial node
            """
            related_links = find_neighbors(link.start_node, original_graph) + \
                            find_neighbors(link.related_to_node, original_graph)
            for node_link in related_links:
                # check if the link is redundant
                if ((node_link.related_to_node == link.related_to_node and
                     node_link.start_node == link.start_node) or (node_link.related_to_node == link.start_node and
                                                                  node_link.start_node == link.related_to_node)) and \
                        node_link.link_tag != "SLINK":
                    single_s_link = False
                    break
            # add single_s_link and remove SLink from the graph
            if single_s_link:
                single_links.add(link)
            original_graph.links.pop(link.get_id_str())

    """
    run a DFS to find the partition yield by the single_s_link
    add the partition to the list of partitions
    """
    for node in original_graph.nodes.values():
        sub_graph = Graph.Graph()
        if node.get_id_str() not in visited_nodes:
            sub_graph = DFS(node, visited_nodes, sub_graph, original_graph)
            sub_graph_list.append(sub_graph)
    # transform the output to a dictionary and return it
    final_form = process_output(sub_graph_list)
    ci.connect_partitions(final_form, len(original_graph.links))
    return final_form


"""
@:arg [Graph], list of all partitions of the TimeML graph
@:returns dict, with the key, value pairs:
                "main_graphs" : [Graph]
                "subordination_graphs" : [Graph]
                "s_links": {Link}
"""


def process_output(graphs: [Graph]) -> dict:
    output = dict()
    main_graphs = []
    graphs[0].type = "main_graph"
    main_length = len(graphs[0].nodes)
    """
    partitions with the largest number of nodes are considered main partitions
    their type is set to main_graph
    """
    for i in range(1, len(graphs)):
        if len(graphs[i].nodes) > len(graphs[i - 1].nodes):
            graphs[i - 1].type = "subordination_graph"
            graphs[i].type = "main_graph"
            main_length = len(graphs[i].nodes)
        elif len(graphs[i].nodes) == main_length:
            graphs[i].type = "main_graph"
        else:
            graphs[i].type = "subordination_graph"
    """
    main partitions are removed from the original list of partitions
    and store in a new one
    """
    for graph in graphs:
        if graph.type == "main_graph":
            main_graphs.append(graph)
            graphs.remove(graph)

    # populate the dictionary
    output["main_graphs"] = main_graphs
    output["subordination_graphs"] = graphs
    output["s_links"] = single_links
    return output


"""
@:arg Node, initial node whose neighbors we wish to find 
@:arg Graph, original TimeML Graph
@:returns [Link], list of links related to the node
"""


def find_neighbors(node, graph: Graph) -> list[Link]:
    neighbors = []
    if type(node) is str:
        node = graph.nodes[node]

    for l in graph.links.values():
        if (graph.nodes[l.start_node].get_id_str() == node.get_id_str()) or (
                graph.nodes[l.related_to_node].get_id_str() == node.get_id_str()):
            neighbors.append(l)
    return neighbors


"""
@:arg Node, initial node whose partition is to be found
@:arg set() of Node objects, nodes that have already been visited in the DFS
@:arg Graph, the partition where the initial node is
@:arg Graph, original TimeML graph
@:returns Graph, subgraph representing the partition where the node is 
"""


def DFS(node, visited_nodes, sub_graph: Graph, original_graph: Graph) -> Graph:
    if type(node) is str:
        visited_nodes.add(node)
        sub_graph.nodes[node] = original_graph.nodes[node]
    else:
        visited_nodes.add(node.get_id_str())
        sub_graph.nodes[node.get_id_str()] = node

    for link in find_neighbors(node, original_graph):
        if link not in sub_graph.links.values():
            sub_graph.links[link.get_id_str()] = link
        if link.related_to_node not in visited_nodes:
            DFS(link.related_to_node, visited_nodes, sub_graph, original_graph)
        if link.start_node not in visited_nodes:
            DFS(link.start_node, visited_nodes, sub_graph, original_graph)
    return sub_graph


"""
@:returns set, the the set of single s_links
"""


def partitionLinks():
    if len(single_links) <= 0:
        print("Please partition a TimeML Graph first.")
        return None
    else:
        return single_links
