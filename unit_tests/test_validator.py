"""
Unit tests.

Command to run from the project root:
    python -m unittest unit_tests.test_validator
"""
import os
import unittest
from lxml import etree
import validator

TEST_TML_DIR = os.path.join(os.path.dirname(__file__), "test_validator_tml")


class UnitTests(unittest.TestCase):
    """
    Minimum-valid TML
    """

    def testWellFormedXml(self):
        with open(os.path.join(TEST_TML_DIR, "pass", "minimum_valid.tml"), 'rb') as f:
            # A well-formed file parses without raising XMLSyntaxError.
            etree.fromstring(f.read())

    def testMinPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "minimum_valid.tml"))
        self.assertTrue(result[0], result)

    """
    Per the TimeML spec, every EVENT must have at least one corresponding
    MAKEINSTANCE; a MAKEINSTANCE whose @eventID points to a non-existent
    EVENT also fails (XSD keyref).
    """

    def testEventWithTwoMakeinstancesPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "event_with_two_makeinstances.tml"))
        self.assertTrue(result[0], result)

    def testEventWithoutMakeinstanceFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "event_no_makeinstance.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("EVENT 'e1' has no corresponding MAKEINSTANCE", result[1], result)

    def testMakeinstanceWithoutEventFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "makeinstance_no_event.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("event_id", result[1], result)

    """
    The schema requires id uniqueness and the pattern letter+digits, but
    not sequential numbering. Gaps in eid/eiid numbering must be accepted.
    """

    def testNonSequentialEventsPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "non_sequential_events.tml"))
        self.assertTrue(result[0], result)

    def testNonSequentialMakeinstancesPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "non_sequential_makeinstances.tml"))
        self.assertTrue(result[0], result)

    def testNoTextTagFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "no_text_tag.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("Tag 'TEXT' expected", result[1], result)

    """
    Test links
    """

    def testTlinkEventEventPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "tlink_event_event.tml"))
        self.assertTrue(result[0], result)

    def testTlinkEventTimex3Passes(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "tlink_event_timex3.tml"))
        self.assertTrue(result[0], result)

    def testTlinkTimex3EventPasses(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "tlink_timex3_event.tml"))
        self.assertTrue(result[0], result)

    def testTlinkTimex3Timex3Passes(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "pass", "tlink_timex3_timex3.tml"))
        self.assertTrue(result[0], result)

    def testTlinkEventTimex3WrongSourceAttribFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_event_timex3_wrong_source_attrib.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("attribute timeID='ei1': value doesn't match any pattern", result[1], result)

    def testTlinkEventTimex3WrongTargetAttribFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_event_timex3_wrong_target_attrib.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("attribute relatedToEventInstance='t1': value doesn't match any pattern", result[1], result)

    def testTlinkTimex3EventWrongSourceAttribFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_timex3_event_wrong_source_attrib.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("attribute eventInstanceID='t1': value doesn't match any pattern", result[1], result)

    def testTlinkTimex3EventWrongTargetAttribFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_timex3_event_wrong_target_attrib.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("attribute relatedToTime='ei1': value doesn't match any pattern", result[1], result)

    def testTlinkEventEventWrongSourceValueFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_event_event_wrong_source_value.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("value ('ei3',) not found for XsdKey", result[1], result)

    def testTlinkEventEventWrongTargetValueFails(self):
        result = validator.validateFile(os.path.join(TEST_TML_DIR, "fail", "tlink_event_event_wrong_target_value.tml"))
        self.assertFalse(result[0], result)
        self.assertIn("value ('ei3',) not found for XsdKey", result[1], result)


if __name__ == "__main__":
    unittest.main()
