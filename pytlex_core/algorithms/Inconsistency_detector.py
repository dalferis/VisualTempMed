"""
Provides methods for identifying inconsistent subgraphs.

A TimeML graph might not be solvable when formulated as a TCSP because of inconsistencies
in the graph. Among these inconsistencies we find self loops, 2 nodes inconsistencies etc.
InconsistencyDetector provide static methods to verify the consistency of a graph and also,
in the case of inconsistencies, generate the subgraphs of inconsistencies.
**
"""
import pytlex_core
from pytlex_core.algorithms import Z3_tcsp_solver
from pytlex_core.data.Graph import Graph
from pytlex_core.data.Link import Link


def detect_self_loop_for_graph(graph: Graph) -> set[Link]:
    """
    Traverses through the links in a graph and returns a
    set of any links that self-loop.
    pMake sure that the links are not of rel_tye SIMULTANEOUS or IDENTITY
    """
    if graph is None:
        raise Exception('Graph cannot be None')

    self_looping_links = set()
    for link in graph.links.values():
        if __is_self_loop(link):
            self_looping_links.add(link)
    return self_looping_links


def is_consistent(graph: Graph) -> bool:
    """
    A static method to verify the consistency of a graph. This is done by trying to solve
    the TCSP presented by the graphs links and nodes. If there is a solution to the TCSP
    then the graph is consistent, otherwise is inconsistent.

    **UPDATED to use Z3_tcsp_solver instead of TCSP_solver**
    """
    if graph is None:
        raise Exception('Graph cannot be None')

    for link in graph.links.values():
        if "S" in link.link_tag:
            raise Exception("Graph cannot have S-Link")

    solution = Z3_tcsp_solver.solve(graph)

    if solution is None:
        return False
    return len(solution) != 0


# helper function to detect if a link is a self loop
def __is_self_loop(link: Link) -> bool:
    return link.start_node == link.related_to_node and ('SIMULTANEOUS' not in link.rel_type) and (
            'IDENTITY' not in link.rel_type)


def generate_self_looping_subgraphs(links: [Link], original_graph: Graph) -> {Graph}:
    """
    Creates a graph containing only the immediate nodes from a given link.
    """
    if links is None:
        raise Exception('The set of links cannot be None')

    return {__make_graph_from_link(link, original_graph) for link in links if __is_self_loop(link)}


# helper function to create a graph from a link
def __make_graph_from_link(_link: Link, original_graph: Graph) -> Graph:
    g = Graph()

    __add_link_to_graph(g, _link, original_graph)

    return g


# helper function to add an edge to a graph
def __add_link_to_graph(_graph: Graph, _edge: Link, original_graph: Graph):
    start_node = original_graph.nodes.get(_edge.start_node)
    related_node = original_graph.nodes.get(_edge.related_to_node)
    if start_node is pytlex_core.data.Instance.Instance:
        _graph.events.update({start_node.event: original_graph.events.get(start_node.event)})
    if related_node is pytlex_core.data.Instance.Instance:
        _graph.events.update({related_node.event: original_graph.events.get(related_node.event)})

    _graph.nodes.update({_edge.start_node: original_graph.nodes.get(_edge.start_node)})
    _graph.nodes.update({_edge.related_to_node: original_graph.nodes.get(_edge.related_to_node)})
    _graph.links.update({_edge.get_id_str(): _edge})


def generate_inconsistent_subgraphs(graph: Graph) -> set[Graph]:
    """
    Given a TimeML graph with inconsistencies, generate a set of subgraphs
    that contain all the links and nodes involved in the inconsistencies that are
    present on the TimeML graph.
    :rtype: object
    """

    if graph is None:
        raise Exception('Graph cannot be None')

    # verify at least one inconsistency exists.
    if is_consistent(graph):
        return set()  # no inconsistencies in this graph.

    # first generate self looping subgraphs
    inconsistent_subgraphs = generate_self_looping_subgraphs(graph.links.values(), graph)

    sub_graph = Graph()
    for event in graph.events.values():
        sub_graph.events.update({event.get_id_str(): event})
    for node in graph.nodes.values():
        sub_graph.nodes.update({node.get_id_str(): node})

    # generate links that are not self loops, is currently a set {}, do we want to change to list []?
    links = {link for link in graph.links.values() if not __is_self_loop(link)}

    inconsistent_links = list()
    consistent_links = list()

    # add all links to the subgraph and save their state
    for link in links:
        sub_graph.links.update({link.get_id_str(): link})

        if is_consistent(sub_graph):
            consistent_links.append(link)
        else:
            sub_graph.links.pop(link.get_id_str())
            inconsistent_links.append(link)

    # for each inconsistent link, create an inconsistent cycle
    for inconsistent_link in inconsistent_links:
        inconsistent_cycle = __complete_inconsistent_cycle(__make_graph_from_link(inconsistent_link, graph),
                                                           consistent_links, graph)

        if inconsistent_cycle is None:
            raise Exception

        inconsistent_subgraphs.add(inconsistent_cycle)

        cycle_links = [inconsistent_cycle.links[key] for key in inconsistent_cycle.links.keys()]
        cycle_links.remove(inconsistent_link)

        for link in cycle_links:
            shared_cycle = __complete_inconsistent_cycle(__make_graph_from_link(link, graph),
                                                         [L for L in consistent_links if L.link_id != link.link_id],
                                                         graph)
            if shared_cycle is not None:
                inconsistent_subgraphs.add(shared_cycle)

    return inconsistent_subgraphs


def __complete_inconsistent_cycle(inconsistent_cycle: Graph, consistent_links: [Link], original_graph: Graph) -> Graph:
    if not is_consistent(inconsistent_cycle):
        return inconsistent_cycle

    # clone the graph
    subgraph = Graph()
    for link in inconsistent_cycle.links.values():
        subgraph.links.update({link.get_id_str(): link})

    for node in inconsistent_cycle.nodes.values():
        subgraph.nodes.update({node.get_id_str(): node})

    for event in inconsistent_cycle.events.values():
        subgraph.events.update({event.get_id_str(): event})

    for link in consistent_links:
        __add_link_to_graph(subgraph, link, original_graph)

        if not is_consistent(subgraph):

            __add_link_to_graph(inconsistent_cycle, link, original_graph)

            return __complete_inconsistent_cycle(inconsistent_cycle,
                                                 [L for L in consistent_links if L.link_id is not link.link_id],
                                                 original_graph)

    return None
