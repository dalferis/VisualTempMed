"""
Unit tests for date-derived ordering links (dateLinks.infer_date_links).

Run from the project root:
    python -m unittest unit_tests.test_datelinks

These don't need Qt: infer_date_links works on the pytlex Graph/TLEX only.
"""
import os
import unittest

from pytlex_core.data import Graph
import dateLinks

TEST_TML_DIR = os.path.join(os.path.dirname(__file__), "test_datelinks_tml")


def readTml(name):
    with open(os.path.join(TEST_TML_DIR, name), encoding="utf-8") as f:
        return f.read()


def infer(tml):
    return dateLinks.infer_date_links(Graph.Graph(time_ml_string=tml))


def triples(links):
    return {(l.start_node, l.rel_type, l.related_to_node) for l in links}


class DateLinkTests(unittest.TestCase):

    def testBeforeInferred(self):
        # Two lone dated timexes, no annotated order between them.
        self.assertEqual(triples(infer(readTml("two_dates.tml"))), {("t1", "BEFORE", "t2")})

    def testSimultaneousInferred(self):
        # Same date -> SIMULTANEOUS.
        self.assertEqual(triples(infer(readTml("same_date.tml"))), {("t1", "SIMULTANEOUS", "t2")})

    def testUnknownValueNotCompared(self):
        # One concrete date and one unknown (XXXX) -> not comparable.
        self.assertEqual(infer(readTml("one_unknown.tml")), [])

    def testContradictionRejected(self):
        # Dates say t1<t2, but an annotated TLINK says t2 BEFORE t1 -> contradiction.
        self.assertEqual(infer(readTml("contradiction.tml")), [])

    def testRedundantWithAnnotatedSkipped(self):
        # t1 BEFORE t2 is already annotated (lid1); the date link t1<t2 would only
        # duplicate it, so it must be skipped. t3 (later, no annotated relation) still
        # gets a date link. (Mirrors EN100700, where annotated t5 BEFORE t7 was duplicated.)
        result = triples(infer(readTml("already_linked.tml")))
        self.assertNotIn(("t1", "BEFORE", "t2"), result)
        self.assertIn(("t2", "BEFORE", "t3"), result)

    def testModalMergeForbidden(self):
        # ei2 (with t2) is MODAL-subordinated to ei1 (with t1): the date link t1<t2
        # would merge a non-factual partition -> forbidden.
        self.assertEqual(infer(readTml("modal_subordination.tml")), [])

    def testEvidentialMergeAllowed(self):
        # Same shape as modal, but EVIDENTIAL subordination: merging it onto the
        # timeline is allowed (reported-as-happened), so the date link is inferred.
        self.assertEqual(triples(infer(readTml("evidential_subordination.tml"))), {("t1", "BEFORE", "t2")})

    def testLinksAreMarkedSyntheticTlinks(self):
        links = infer(readTml("two_dates.tml"))
        self.assertTrue(links)
        for l in links:
            self.assertEqual(l.link_tag, "TLINK")
            self.assertTrue(getattr(l, "_date_inferred", False))


if __name__ == "__main__":
    unittest.main()
