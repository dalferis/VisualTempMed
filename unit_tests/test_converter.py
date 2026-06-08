"""
Unit tests for E3C -> TimeML conversion (converter.py).

All test inputs are minimal E3C XMI files under unit_tests/test_converter_tml/,
each focused on one aspect of the conversion (metadata, events, timex3).
The converter validates its output internally against the XSD and the TimeML
spec, so a passing convertContent return is also a validation pass.

Run from the project root:
    python -m unittest unit_tests.test_converter
"""
import os
import unittest

import converter

TEST_TML_DIR = os.path.join(os.path.dirname(__file__), "test_converter_tml")


def convertInput(name):
    with open(os.path.join(TEST_TML_DIR, name), encoding="utf-8") as f:
        return converter.convertContent(f.read())


class ConverterTests(unittest.TestCase):

    # --- metadata.xml: only METADATA, no annotations --------------------

    def testMetadataProducesDct(self):
        result = convertInput("metadata.xml")
        self.assertTrue(result[0], result)
        tml = result[1]
        # docTime="2020-01-15" -> <DCT><TIMEX3 tid="t0" type="DATE"
        # value="2020-01-15T00:00:00" functionInDocument="CREATION_TIME" .../>
        self.assertIn('<DCT>', tml)
        self.assertIn('tid="t0"', tml)
        self.assertIn('type="DATE"', tml)
        self.assertIn('functionInDocument="CREATION_TIME"', tml)
        self.assertIn('value="2020-01-15T00:00:00"', tml)

    def testMetadataHasNoOtherAnnotations(self):
        # No EVENT/TIMEX3/TLINK/SLINK present in the source -> none emitted.
        # The only TIMEX3 in the output is the DCT (t0).
        tml = convertInput("metadata.xml")[1]
        self.assertNotIn('<EVENT ', tml)
        self.assertNotIn('<MAKEINSTANCE', tml)
        self.assertNotIn('<TLINK', tml)
        self.assertNotIn('<SLINK', tml)
        self.assertNotIn('<ALINK', tml)
        # No TIMEX3 type other than the DATE of the DCT.
        for t in ('TIME', 'DURATION', 'SET'):
            self.assertNotIn(f'type="{t}"', tml)

    # --- events.xml: all eventType values + BEGINS-ON/ENDS-ON TLINKs ----

    def testEventTypeMappings(self):
        # E3C eventType -> TimeML class:
        #   N/A         -> OCCURRENCE   (admitted)
        #   ASPECTUAL   -> ASPECTUAL    (begins)
        #   EVIDENTIAL  -> REPORTING    (reported)
        result = convertInput("events.xml")
        self.assertTrue(result[0], result)
        tml = result[1]
        self.assertIn('class="OCCURRENCE"', tml)
        self.assertIn('class="ASPECTUAL"', tml)
        self.assertIn('class="REPORTING"', tml)

    def testEventClassNoUnusedEnumerations(self):
        # The converter never emits I_ACTION, I_STATE or PERCEPTION because
        # they have no E3C equivalent. STATE is only produced when
        # contextualModality=GENERIC or permanence=PERMANENT override an
        # OCCURRENCE, neither of which is present in events.xml.
        tml = convertInput("events.xml")[1]
        for cls in ('STATE', 'I_ACTION', 'I_STATE', 'PERCEPTION'):
            self.assertNotIn(f'class="{cls}"', tml)

    def testHedgedAddsModalityMay(self):
        # contextualModality=HEDGED on the first event ("admitted")
        # -> MAKEINSTANCE modality="may".
        tml = convertInput("events.xml")[1]
        self.assertIn('modality="may"', tml)

    def testDocTimeRelTlinks(self):
        # docTimeRel=BEFORE/OVERLAP/AFTER -> TLINK relType
        # BEFORE/SIMULTANEOUS/AFTER, each anchored to the DCT (t0).
        tml = convertInput("events.xml")[1]
        self.assertIn('relType="BEFORE"', tml)
        self.assertIn('relType="SIMULTANEOUS"', tml)
        self.assertIn('relType="AFTER"', tml)
        # All three docTimeRel TLINKs target t0.
        self.assertEqual(tml.count('relatedToTime="t0"'), 3)

    def testBeginsOnEndsOnMapping(self):
        # E3C BEGINS-ON / ENDS-ON (THYME: this event's start/end is anchored
        # to another event) -> TimeML IAFTER / IBEFORE.
        # NOT BEGINS / ENDS, which would wrongly assert a shared boundary
        # plus a spurious constraint on the other endpoint.
        tml = convertInput("events.xml")[1]
        self.assertIn('relType="IAFTER"', tml)
        self.assertIn('relType="IBEFORE"', tml)
        # The wrong mapping must NOT be present.
        self.assertNotIn('relType="BEGINS"', tml)
        self.assertNotIn('relType="ENDS"', tml)

    def testTlinkNoUnusedRelTypes(self):
        # events.xml exercises BEFORE/OVERLAP/AFTER (docTimeRel) and
        # BEGINS-ON/ENDS-ON (EVENTTLINKLink). No other TLINK relType should
        # appear (ALINK relTypes are checked separately).
        tml = convertInput("events.xml")[1]
        for rel in ('INCLUDES', 'IS_INCLUDED',
                    'BEGINS', 'ENDS', 'BEGUN_BY', 'ENDED_BY',
                    'DURING', 'DURING_INV', 'IDENTITY'):
            self.assertNotIn(f'relType="{rel}"', tml)

    def testAlinkRoleMappings(self):
        # E3C EVENTALINKLink role passes through directly to TimeML ALINK
        # relType (no semantic translation). All four role values are
        # exercised on the "begins" event.
        tml = convertInput("events.xml")[1]
        self.assertIn('<ALINK ', tml)
        for role in ('INITIATES', 'CONTINUES', 'REINITIATES', 'TERMINATES'):
            self.assertIn(f'relType="{role}"', tml)

    # --- timex3.xml: all timex3Class values -----------------------------

    def testTimex3ClassMappings(self):
        # E3C timex3Class -> TimeML type:
        #   DATE        -> DATE       (2020-01-01)
        #   TIME        -> TIME       (10:00)
        #   DURATION    -> DURATION   (P5D)
        #   SET         -> SET        (each year)
        #   QUANTIFIER  -> SET        (twice, with e3c:timex3Class=QUANTIFIER)
        #   PREPOSTEXP  -> DURATION   (post-op, value forced to PXD)
        result = convertInput("timex3.xml")
        self.assertTrue(result[0], result)
        tml = result[1]
        self.assertIn('type="DATE"', tml)
        self.assertIn('type="TIME"', tml)
        self.assertIn('type="DURATION"', tml)
        self.assertIn('type="SET"', tml)

    def testPrepostexpForcedToPxd(self):
        tml = convertInput("timex3.xml")[1]
        self.assertIn('value="PXD"', tml)
        # PREPOSTEXP and NO_VALUE are preserved as comments on the timex3.
        self.assertIn('e3c:timex3Class=PREPOSTEXP', tml)
        self.assertIn('e3c:value=NO_VALUE', tml)

    def testQuantifierApproximatedToSet(self):
        # QUANTIFIER has no TimeML equivalent; we approximate to SET and
        # record the loss in the comment.
        tml = convertInput("timex3.xml")[1]
        self.assertIn('e3c:timex3Class=QUANTIFIER', tml)

    def testTimex3NoE3cOnlyTypeLeaksThrough(self):
        # PREPOSTEXP and QUANTIFIER are E3C-only enumerations; they must not
        # appear as TimeML type values. Only DATE/TIME/DURATION/SET are
        # legal in the TimeML XSD.
        tml = convertInput("timex3.xml")[1]
        self.assertNotIn('type="PREPOSTEXP"', tml)
        self.assertNotIn('type="QUANTIFIER"', tml)

    def testTimex3TimexLinkMappings(self):
        # E3C TIMEX3TimexLinkLink role -> TimeML TLINK relType:
        #   BEFORE      -> BEFORE        (t1 BEFORE t2)
        #   CONTAINS    -> INCLUDES      (t1 CONTAINS t3)
        #   OVERLAP     -> SIMULTANEOUS  (t2 OVERLAP t4, with e3c:role comment)
        #   BEGINS-ON   -> IAFTER        (t3 BEGINS-ON t5)
        #   ENDS-ON     -> IBEFORE       (t3 ENDS-ON t6)
        tml = convertInput("timex3.xml")[1]
        for rel in ('BEFORE', 'INCLUDES', 'SIMULTANEOUS', 'IAFTER', 'IBEFORE'):
            self.assertIn(f'relType="{rel}"', tml)
        # TIMEX3-to-TIMEX3 TLINKs use timeID / relatedToTime, not
        # eventInstanceID / relatedToEventInstance.
        self.assertIn('timeID="t1"', tml)
        self.assertNotIn('eventInstanceID=', tml)
        self.assertNotIn('relatedToEventInstance=', tml)

    def testTimex3TlinkNoUnusedRelTypes(self):
        # timex3.xml exercises BEFORE/CONTAINS/OVERLAP/BEGINS-ON/ENDS-ON.
        # AFTER, IS_INCLUDED and the BEGINS/ENDS family should not appear.
        tml = convertInput("timex3.xml")[1]
        for rel in ('AFTER', 'IS_INCLUDED',
                    'BEGINS', 'ENDS', 'BEGUN_BY', 'ENDED_BY',
                    'DURING', 'DURING_INV', 'IDENTITY'):
            self.assertNotIn(f'relType="{rel}"', tml)


if __name__ == "__main__":
    unittest.main()
