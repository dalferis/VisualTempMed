import unittest

from pytlex_core.algorithms.TLEX import TLEX
from pytlex_core.data.Graph import Graph
from pytlex_core.timeline.Timeline import find_timeline
from pytlex_tests import Testing_utilities
import json


class Graph_test(unittest.TestCase):
    def test_single(self):
        print("\n")
        for link in Testing_utilities.consistent_graph_2().links:
            print(link)

    def test_non_single(self):
        # Testing on a known .tml file
        print("Filename: wsj_0006")
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)

        # Testing to see if graph contains correct number of nodes and links
        self.assertEqual(len(graph.links.values()), 13)
        self.assertEqual(len(graph.nodes.values()), 11)
        # Test if graph is consistent (it should be)
        self.assertTrue(graph.consistency)
        # Test if metadata is identified correctly
        self.assertEqual(len(graph.metadata), 9)

        # Test to_json
        print("Graph in json format:")
        print(graph.to_json())
        # print(json.dumps(json.loads(graph.to_json()), indent=4, sort_keys=True))


        # If given anything but a formatted tml file/string, should raise an exception
        filepath = r"../pytlex_core/__init__.py"
        with self.assertRaises(Exception):  # Should return true
            bad_graph = Graph(filepath=filepath)

        # It should be able to make a graph out of every .tml file in the corpus without errors
        filepath = r"../pytlex_data/TimeBankCorpus"
        # Dont test UNLESS you have ~4 mins to spare
        # for subdir, dirs, files in os.walk(filepath):
        #     for filename in files:
        #         test_graph = Graph(filepath=(filepath + "/" + filename))

    def test_json(self):
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        print(graph.to_json())

if __name__ == '__main__':
    unittest.main()