# edited by gparr014
"""

Takes around: 8 minutes 5 seconds
Solve test takes up around 8 min 2 seconds of that as it tests entire corpus
"""

import unittest
import os

import pytlex_core.algorithms.TLEX
from pytlex_core.algorithms import IndeterminacyDetector, TLEX
from pytlex_core.data import Graph, Link
from pytlex_tests import Testing_utilities


class IndeterminacyDetectorTest(unittest.TestCase):
    # test each individual method
    def test_solve(self):
        # test the entire corpus
        corpus_path = r'../pytlex_data/TimeBankCorpus'
        corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]

        for file in corpus_files:
            g = Graph.Graph(filepath=corpus_path + '/' + file)
            tlex = TLEX.TLEX(graph=g)
            print(f'{file}\t{tlex.indeterminacy_score}',flush=True)

    # test method total_time_points()
    # first with a 2 item list, then 0
    def test_total_time_points(self):
        t_case1 = {"key1": ["s1", "s2"]}
        t_case2 = {}
        self.assertEqual(IndeterminacyDetector.total_time_points(t_case1), 2)
        self.assertEqual(IndeterminacyDetector.total_time_points(t_case2), 0)

    # tests a link between nodes
    def test_link_between(self):
        # manual nodes to test if they are related
        t1 = Testing_utilities.test_timex(1)
        t2 = Testing_utilities.test_timex(2)
        t3 = Testing_utilities.test_timex(3)

        l1 = Link.Link(1, "TLINK", "BEFORE", t1.get_id_str(), t2.get_id_str())
        l2 = Link.Link(2, "TLINK", "BEFORE", t3.get_id_str(), t2.get_id_str())

        test_g = Graph.Graph(nodes={t1, t2, t3}, links={l1, l2})
        print(test_g.links)
        print(test_g.nodes)
        print(IndeterminacyDetector.link_between("t1", "t2", test_g))
        self.assertEqual(IndeterminacyDetector.link_between("t1", "t2", test_g), True)
        self.assertEqual(IndeterminacyDetector.link_between("t1", "t3", test_g), False)

    # solve starting from timepoint1 and timepoint2
    def test_solve_with_new_constraint(self):
        # make a test graph that has 6 links
        t1 = Testing_utilities.test_timex(1)
        t2 = Testing_utilities.test_timex()
        t3 = Testing_utilities.test_timex()
        t4 = Testing_utilities.test_timex()
        t5 = Testing_utilities.test_timex()
        t6 = Testing_utilities.test_timex()

        l1 = Link.Link(1, "TLINK", "BEFORE", t1.get_id_str(), t2.get_id_str())
        l2 = Link.Link(2, "TLINK", "BEFORE", t3.get_id_str(), t2.get_id_str())
        l3 = Link.Link(3, "TLINK", "BEGUN_BY", t4.get_id_str(), t3.get_id_str())
        l4 = Link.Link(4, "TLINK", "BEFORE", t4.get_id_str(), t5.get_id_str())
        l5 = Link.Link(5, "TLINK", "INCLUDES", t5.get_id_str(), t6.get_id_str())

        test_g = Graph.Graph({t1, t2, t3, t4, t5, t6}, {l1, l2, l3, l4, l5})

        # if the graph is None, make sure the exception is caught
        with self.assertRaises(Exception):
            IndeterminacyDetector.solve_with_new_constraint(None, False, "t1", "t2")

        # test empty starting points
        with self.assertRaises(Exception):
            IndeterminacyDetector.solve_with_new_constraint(test_g, False, "", "")

        # if timepoint1 == timepoint2, it should return True
        self.assertEqual(IndeterminacyDetector.solve_with_new_constraint(test_g, True, "t1", "t1"), True)

        # if timepoint1 != timepoint2 and flag is False return True
        self.assertEqual(IndeterminacyDetector.solve_with_new_constraint(test_g, False, "t1", "t2"), True)

    def test_indeterminacy_file(self):
        g = Graph.Graph(None, None, None, None, r"../pytlex_data/TimeBankCorpus/wsj_1073.tml", None)
        tlex = TLEX.TLEX(graph=g)
        print("Indeterminacy Score: ", tlex.indeterminacy_score)


if __name__ == '__main__':
    unittest.main()
