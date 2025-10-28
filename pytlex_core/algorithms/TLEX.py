"""
The Entry Point for pyTLEX. Is meant to take in a Graph and partition the Graph
before it solves it for its Indeterminacy, Consistency, and its Timelines.

The Class can grab a TimeMLGraph's consistent/inconsistent partitions, as well as the Timelines.
"""
from dataclasses import dataclass, field

from pytlex_core.algorithms import Partitioner, IndeterminacyDetector, Inconsistency_detector
from pytlex_core.data import Graph
from pytlex_core.timeline import Timeline
from pytlex_core.timeline.Indeterminacy import Indeterminacy
from pytlex_core.timeline.Timeline import find_timeline
from pytlex_core.timeline.TrunkAndBranch import TrunkAndBranch


@dataclass
class TLEX:
    """
    A Class meant for holding the final set of information after solving a TimeMLGraph.

    It contains the Graph, its separate partitions, indeterminacy score, indeterminant timepoints,
    the indeterminant timepairs, the trunk and branch structure of the graph's timelines, as well
    as suggested links and SLINKs.
    """
    graph: Graph = field(default=None)
    partitions: dict = field(default_factory=dict)
    indeterminacy_score: float = field(default=-1.0)
    indeterminant_time_points: set = field(default=())
    indeterminant_sections: set = field(default=())
    indeterminant_time_pairs: list = field(default_factory=list)
    timeline: TrunkAndBranch = field(default=None)
    suggested_links: list = field(default_factory=list)
    s_links: list = field(default_factory=list)
    indeterminacy_results: Indeterminacy = field(default=None)

    def __post_init__(self):
        # partitioner manipulates the node and link sets, so we hold onto these sets for later restoration
        self.graph.prepartitioned_links = self.graph.links.copy()
        self.graph.prepartitioned_nodes = self.graph.nodes.copy()

        self.partitions = Partitioner.partition_graph(self.graph)
        self.main_graphs = self.partitions['main_graphs']
        self.subordination_graphs = self.partitions['subordination_graphs']
        self.s_links = self.partitions['s_links']
        self.suggested_links = self.partitions['suggested_links']
        del self.partitions['s_links']
        del self.partitions['suggested_links']

        self.graph.consistency = True

        max = 0
        main_graph = None
        for index, graph in enumerate(self.main_graphs):
            if len(graph.nodes) > max:
                max = len(graph.nodes)
                main_graph = graph

        for graph in self.main_graphs[:]:
            if graph != main_graph:
                self.subordination_graphs.append(graph)
                self.main_graphs.remove(graph)

        self.indeterminacy_results = IndeterminacyDetector.solve(
            self.graph)

        timelines = []
        for partition in self.main_graphs + self.subordination_graphs:
            solved_timeline = find_timeline(partition)
            timeline = None
            if solved_timeline is not None:
                timeline = Timeline.Timeline(timeline=solved_timeline)
                timelines.append(timeline)

            if timeline is not None:
                self.graph.total_time_points += timeline.get_total_timepoints()

            if not partition.consistency:
                self.graph.consistency = False

        self.timeline = TrunkAndBranch(timelines, self.s_links)

        # nodes and links are restored here
        self.graph.nodes = self.graph.prepartitioned_nodes
        self.graph.links = self.graph.prepartitioned_links
        del self.graph.prepartitioned_links
        del self.graph.prepartitioned_nodes

    def get_consistent_partitions(self):
        # Grabs all consistent partitions found in a graph
        consistent_partitions = []
        for partition in self.main_graphs + self.subordination_graphs:
            if partition.consistency is True:
                consistent_partitions.append(partition)
        return consistent_partitions

    def get_inconsistent_partitions(self):
        # Grabs all inconsistent partitions found in a graph
        inconsistent_partitions = []
        for partition in self.main_graphs + self.subordination_graphs:
            if partition.consistency is False:
                inconsistent_partitions.append(partition)
        return inconsistent_partitions

    def get_indeterminacy_score(self):
        main_results = IndeterminacyDetector.solve(graph=self.graph)
        print("\nParent Graph Indeterminacy Score: ", main_results.score)
        for graph in self.main_graphs + self.subordination_graphs:
            partition_results = IndeterminacyDetector.solve(graph=graph)
            print("SubGraph Indeterminacy Score: ", partition_results.score)

    def to_json(self):
        ret = "{\"nodes\":["
        for node in self.graph.nodes.values():
            ret += node.to_json() + ","

        ret = ret[:-1] + "],\"links\":["
        if not self.graph.links:
            ret += ","
        for link in self.graph.links.values():
            ret += link.to_json() + ","

        ret = ret[:-1] + "],\"events\":["
        if not self.graph.events:
            ret += ","
        for event in self.graph.events.values():
            ret += event.to_json() + ","

        ret = ret[:-1] + "],\"signals\":["
        if not self.graph.signals:
            ret += ","
        for signal in self.graph.signals.values():
            ret += signal.to_json() + ","


        ret = ret[:-1] + "],\"partitions\":["
        if not self.partitions:
            ret += ","
        for partition in self.partitions.values():
            if len(partition) > 0:
                ret += self.__partition_as_json(partition[0]) + ","
        ret = ret[:-1] + "],\"isConsistent\":"
        Partitioner.partition_graph(self.graph)
        if Inconsistency_detector.is_consistent(self.graph):
            ret += "true,"
        else:
            ret += "false,"
        ret += "\"inconsistentSubGraphs\":["
        inconsistent_subgraphs = Inconsistency_detector.generate_inconsistent_subgraphs(self.graph)
        if inconsistent_subgraphs:
            for inconsistent_subgraph in inconsistent_subgraphs:
                ret += inconsistent_subgraph.to_json() + ","
            ret = ret[:-1]
        ret += "]}"
        return ret

    def __partition_as_json(self, partition):
        ret = "{\"nodeIds\":["
        for node in partition.nodes:
            ret += "\"" + node + "\","

        ret = ret[:-1] + "],\"linkIds\":["
        if not partition.links:
            ret += ","
        for link in partition.links:
            ret += "\"" + link + "\","
        partition_tlex = TLEX(partition)

        ret = ret[:-1] + "],\"timeline\":"
        if partition_tlex.timeline.trunk is not None:
            ret += partition_tlex.timeline.trunk.to_json()
        else:
            ret += "[]"
        ret = ret + ",\"isConsistent\":"
        if partition.consistency is True:
            ret += "true"
        else:
            ret += "false"
        ret += ",\"indeterminantTimePairs\":["
        time_pairs = partition_tlex.indeterminacy_results.get_indeterminate_time_pairs()
        if not time_pairs:
            ret += ","
        for time_pair in time_pairs:
            ret += "{\"id1\":\""
            point_one = time_pair[0].split("_")
            point_two = time_pair[1].split("_")
            ret += point_one[0] + "\",\"timePoint1\":\""
            if "plus" in point_one[1]:
                ret += "+"
            elif "minus" in point_one[1]:
                ret += "-"
            ret += "\",\"id2\":\"" + point_two[0] + "\",\"timePoint2\":\""
            if "plus" in point_two[1]:
                ret += "+"
            elif "minus" in point_two[1]:
                ret += "-"
            ret += "\"},"

        ret = ret[:-1] + "]}"
        return ret
