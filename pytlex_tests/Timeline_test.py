import unittest

from pytlex_core.algorithms import Partitioner
from pytlex_core.algorithms.TLEX import TLEX
from pytlex_core.data.Graph import Graph
from pytlex_core.timeline.Timeline import Timeline, find_timeline
from pytlex_core.timeline.TrunkAndBranch import TrunkAndBranch
from pytlex_tests import Testing_utilities
import json


class Timelines_test(unittest.TestCase):
    def test_timeline_null(self):
        with self.assertRaises(Exception):
            timeline = Timeline(None)

    def test_trunk_and_branch(self):
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)
        print("\n", tlex.timeline)

    def test_trunk_and_branch_no_links(self):
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        partitions = Partitioner.partition_graph(graph)
        timelines = []
        for partition in partitions['main_graphs'] + partitions['subordination_graphs']:
            solved_timeline = find_timeline(partition)
            timeline = Timeline(timeline=solved_timeline)
            timelines.append(timeline)
        trunk_and_branch = TrunkAndBranch(timelines, None)
        print("\n", trunk_and_branch)

    def test_timeline_points(self):
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)

        print("Timeline: ", tlex.timeline.trunk)
        print("First Point: ", tlex.timeline.trunk.get_first_point())
        print("Last Point: ", tlex.timeline.trunk.get_last_point())
        print("Fifth Point: ", tlex.timeline.trunk.get_timepoints(5))

    def test_node_incoming_links(self):
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980120.1830.0957.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)
        print(tlex.timeline.get_node_incoming_slinks("eiid416"))

    def test_node_outgoing_links(self):
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980120.1830.0957.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)

        print(tlex.timeline.get_node_outgoing_slinks("eiid439"))


    def test_total_timeline(self):
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_0006.tml"
        graph = Graph(filepath=filepath)
        tlex = TLEX(graph=graph)

        print("# of Timelines: ", tlex.timeline.get_total_timelines())
        print("# of Timepoints: ", tlex.timeline.trunk.get_total_timepoints())

if __name__ == '__main__':
    unittest.main()