"""
Unit tests for date-derived ordering links (dateLinks.infer_date_links).

Run from the project root:
    python -m unittest unit_tests.test_datelinks

These don't need Qt: infer_date_links works on the pytlex Graph/TLEX only.
"""
import unittest

from pytlex_core.data import Graph
import dateLinks


def infer(tml):
    return dateLinks.infer_date_links(Graph.Graph(time_ml_string=tml))


def triples(links):
    return {(l.start_node, l.rel_type, l.related_to_node) for l in links}


# Two lone dated timexes, no annotated order between them.
TML_TWO_DATES = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> and <TIMEX3 tid="t2" type="DATE" value="1998-01-11" temporalFunction="false" functionInDocument="NONE">Jan 11</TIMEX3>.</TEXT>
</TimeML>"""

# Same date -> SIMULTANEOUS.
TML_SAME_DATE = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> and <TIMEX3 tid="t2" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">that day</TIMEX3>.</TEXT>
</TimeML>"""

# One concrete date and one unknown (XXXX) -> not comparable.
TML_ONE_UNKNOWN = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> and <TIMEX3 tid="t2" type="DATE" value="XXXX" temporalFunction="true" functionInDocument="NONE">post-op</TIMEX3>.</TEXT>
</TimeML>"""

# Dates say t1<t2, but an annotated TLINK says t2 BEFORE t1 -> contradiction.
TML_CONTRADICTION = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> and <TIMEX3 tid="t2" type="DATE" value="1998-01-11" temporalFunction="false" functionInDocument="NONE">Jan 11</TIMEX3>.</TEXT>
  <TLINK lid="l1" timeID="t2" relatedToTime="t1" relType="BEFORE"/>
</TimeML>"""

# t1 BEFORE t2 is already annotated (lid1); the date link t1<t2 would only
# duplicate it, so it must be skipped. t3 (later, no annotated relation) still
# gets a date link. (Mirrors EN100700, where annotated t5 BEFORE t7 was duplicated.)
TML_ALREADY_LINKED = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT><TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> <TIMEX3 tid="t2" type="DATE" value="1998-01-11" temporalFunction="false" functionInDocument="NONE">Jan 11</TIMEX3> <TIMEX3 tid="t3" type="DATE" value="1998-01-12" temporalFunction="false" functionInDocument="NONE">Jan 12</TIMEX3>.</TEXT>
  <TLINK lid="l1" timeID="t1" relatedToTime="t2" relType="BEFORE"/>
</TimeML>"""

# ei2 (with t2) is MODAL-subordinated to ei1 (with t1): the date link t1<t2
# would merge a non-factual partition -> forbidden.
TML_MODAL = """<?xml version="1.0" encoding="UTF-8"?>
<TimeML>
  <TEXT>He <EVENT eid="e1" class="REPORTING" stem="say">said</EVENT> on <TIMEX3 tid="t1" type="DATE" value="1998-01-10" temporalFunction="false" functionInDocument="NONE">Jan 10</TIMEX3> it might <EVENT eid="e2" class="OCCURRENCE" stem="rain">rain</EVENT> on <TIMEX3 tid="t2" type="DATE" value="1998-01-11" temporalFunction="false" functionInDocument="NONE">Jan 11</TIMEX3>.</TEXT>
  <MAKEINSTANCE eiid="ei1" eventID="e1" tense="PAST" aspect="NONE" polarity="POS" pos="VERB"/>
  <MAKEINSTANCE eiid="ei2" eventID="e2" tense="NONE" aspect="NONE" polarity="POS" pos="VERB"/>
  <TLINK lid="l1" eventInstanceID="ei1" relatedToTime="t1" relType="IS_INCLUDED"/>
  <TLINK lid="l2" eventInstanceID="ei2" relatedToTime="t2" relType="IS_INCLUDED"/>
  <SLINK lid="l3" relType="MODAL" eventInstanceID="ei1" subordinatedEventInstance="ei2"/>
</TimeML>"""

# Same shape, but EVIDENTIAL subordination: merging it onto the timeline is
# allowed (reported-as-happened), so the date link is inferred.
TML_EVIDENTIAL = TML_MODAL.replace('relType="MODAL"', 'relType="EVIDENTIAL"')


class DateLinkTests(unittest.TestCase):

    def testBeforeInferred(self):
        self.assertEqual(triples(infer(TML_TWO_DATES)), {("t1", "BEFORE", "t2")})

    def testSimultaneousInferred(self):
        self.assertEqual(triples(infer(TML_SAME_DATE)), {("t1", "SIMULTANEOUS", "t2")})

    def testUnknownValueNotCompared(self):
        self.assertEqual(infer(TML_ONE_UNKNOWN), [])

    def testContradictionRejected(self):
        self.assertEqual(infer(TML_CONTRADICTION), [])

    def testRedundantWithAnnotatedSkipped(self):
        # t1 BEFORE t2 is annotated -> no duplicate synthetic link for that pair,
        # but t2 BEFORE t3 (no annotated relation) is still inferred.
        result = triples(infer(TML_ALREADY_LINKED))
        self.assertNotIn(("t1", "BEFORE", "t2"), result)
        self.assertIn(("t2", "BEFORE", "t3"), result)

    def testModalMergeForbidden(self):
        self.assertEqual(infer(TML_MODAL), [])

    def testEvidentialMergeAllowed(self):
        self.assertEqual(triples(infer(TML_EVIDENTIAL)), {("t1", "BEFORE", "t2")})

    def testLinksAreMarkedSyntheticTlinks(self):
        links = infer(TML_TWO_DATES)
        self.assertTrue(links)
        for l in links:
            self.assertEqual(l.link_tag, "TLINK")
            self.assertTrue(getattr(l, "_date_inferred", False))


if __name__ == "__main__":
    unittest.main()
