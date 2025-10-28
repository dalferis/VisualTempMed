import os
import unittest

from pytlex_core.algorithms.TLEX import TLEX
from pytlex_core.data.Graph import Graph
from pytlex_core.algorithms.Partitioner import partition_graph,find_neighbors,DFS,partitionLinks
from pytlex_core.data.TimeX import TimeX
from pytlex_tests import Testing_utilities as test_ut, Testing_utilities
from pytlex_tests.jTLEX_Data import jTLEX_Counts

"""
Tester for the Partitioner class. 
Each method partitions a different TimeML Graph.
Partitions are then checked for correctness.

Last test, test_partition_lengths vs jtlex takes around 7 minutes
other tests only take a few seconds
"""
class PartitionerTest(unittest.TestCase):
    error_message = 'Erroneous or unexpected output'

    def test_partition_graph_wsj_0006(self):
        graph = test_ut.wsj_0006()
        print(graph.nodes)

        results = partition_graph(graph)
        print("Filename: wsj_0006")
        for main_partition in results["main_graphs"]:
            print('Main Partition nodes:')
            for n in main_partition.nodes.values():
                print(n.get_id_str())

        print("\n")
        for sub_partition in results["subordination_graphs"]:
            print('Subordination Partition nodes:')
            for n in sub_partition.nodes.values():
                print(n.get_id_str())
        print("\n")

        print("S_links:")
        for l in results["s_links"]:
            print(f'{l.start_node} -> {l.related_to_node}')

    def test_partition_graph_wsj_1073(self):
        graph = test_ut.wsj_1073()

        results = partition_graph(graph)
        print("\nFilename: wsj_1073")
        for main_partition in results["main_graphs"]:
            print('Main Partition nodes:')
            for n in main_partition.nodes.values():
                print(n.get_id_str())
        print("\n")

        for sub_partition in results["subordination_graphs"]:
            print('Subordination Partition nodes:')
            for n in sub_partition.nodes.values():
                print(n.get_id_str())
        print("\n")

        print("S_links:")
        for l in results["s_links"]:
            print(f'{l.start_node} -> {l.related_to_node}')

    def test_partition_graph_wsj_0555(self):
        graph = test_ut.wsj_0555()

        results = partition_graph(graph)
        print("\nFilename: wsj_0555")
        for main_partition in results["main_graphs"]:
            print('Main Partition nodes:')
            for n in main_partition.nodes.values():
                print(n.get_id_str())
        print("\n")
        for sub_partition in results["subordination_graphs"]:
            print('Subordination Partition nodes:')
            for n in sub_partition.nodes.values():
                print(n.get_id_str())
        print("\n")
        print("S_links:")
        for l in results["s_links"]:
            print(f'{l.start_node} -> {l.related_to_node}')

    def test_partition_find_neighbors(self):
        print()
        graph = test_ut.wsj_0006()
        print("Filename: wsj_0006")
        nodes = graph.nodes
        links = graph.links
        nodes_list = list(nodes)
        first_node = nodes_list[0]
        print("The list of nodes for this graph is:")
        for node in nodes :
            print(node)
        print("The list of links for this graph is:")
        for link in links:
            print(link)
        print("Given node:",first_node)
        print("The links related to that node are:")
        for link in find_neighbors(first_node,graph) :
            print(link)
        # We can see that every node is featured in at least 1 link, therefore:
        self.assertTrue(len(find_neighbors(first_node,graph)) > 0)

        # What if the node is not featured in the graph? Should return an empty list
        test_node = TimeX(1, "1998-10-11", True, "howdy", "DATE", "BEFORE", "NONE",
                          None, None, None, None, None)
        self.assertEqual(find_neighbors(test_node, graph),[])
        # What if the graph has no links? Should also return an empty list
        graph.links.clear()
        self.assertEqual(find_neighbors(first_node,graph),[])

    def test_partition_DFS(self):
        print()
        graph = test_ut.wsj_0006()
        results = partition_graph(graph)
        print("Filename: wsj_0006")
        # DFS(node, visited_nodes, sub_graph: Graph, original_graph: Graph)
        visited_nodes = set()
        main_partitions = results["main_graphs"]
        nodes = main_partitions[0].nodes
        nodes_list = list(nodes)
        first_node = nodes_list[0]
        # Given a node and the sub_graph said node belongs to, DFS should return
        # the given sub_graph
        self.assertEqual(DFS(first_node,visited_nodes,main_partitions[0],graph),main_partitions[0])

        # What if the sub_graph and original graph are the same? Should return the orig graph
        self.assertEqual(DFS(first_node,visited_nodes,graph,graph),graph)
        # What if the node is not in the sub_graph? Should return the given sub_graph
        # and have the node now included in said sub_graph and visited_nodes
        test_node = TimeX(1, "1998-10-11", True, "howdy", "DATE", "BEFORE", "NONE",
                          None, None, None, None, None)
        self.assertEqual(DFS(test_node,visited_nodes,main_partitions[0],graph),main_partitions[0])
        self.assertTrue(test_node in main_partitions[0].nodes.values())
        self.assertTrue(test_node.get_id_str() in visited_nodes)
        # What if the node is already in visited_nodes? Should return the sub_graph
        # and visited_nodes should remain unchanged
        visited_nodes_old = visited_nodes
        self.assertEqual(DFS(test_node, visited_nodes, main_partitions[0], graph), main_partitions[0])
        self.assertEqual(visited_nodes_old, visited_nodes)
        # What if the original graph has no links nor nodes? Should just return the sub_graph
        self.assertEqual(DFS(test_node,visited_nodes,main_partitions[0],graph),main_partitions[0])
        self.assertEqual(DFS(test_node, visited_nodes, graph, graph), graph)


    def test_a_partition_partitionLinks(self):
        print()
        # If not graph has been partitioned, should print an error
        # message and return None
        self.assertEqual(partitionLinks(),None)
        # Otherwise, should return the same list of single SLinks as
        # that stored in the partition dictionary
        graph = test_ut.wsj_0006()
        results = partition_graph(graph)
        self.assertEqual(results["s_links"],partitionLinks())

    def test_partition_lengths_vs_jtlex(self):
        filepath = r"../pytlex_data/TimeBankCorpus"
        for subdir, dirs, files in os.walk(filepath):
            for filename in files:
                if filename not in Testing_utilities.failed_parse:
                    graph = Graph(filepath=filepath + "/" + filename)
                    tlex = TLEX(graph=graph)
                    self.assertEqual(
                        len(tlex.main_graphs + tlex.subordination_graphs),
                        jTLEX_Counts.jTLEX_partition_counts[filename]
                    )


if __name__ == '__main__':
    unittest.main()
