"""
Unit tests for E3C -> TimeML conversion (converter.py).

Run from the project root:
    python -m unittest unit_tests.test_converter
"""
import os
import re
import unittest

import converter
import validator

EN100017 = os.path.join("E3C-Corpus", "data_annotation", "English", "layer1", "EN100017.xml")


class ConverterTests(unittest.TestCase):

    def testBeginsOnEndsOnMapping(self):
        # E3C BEGINS-ON / ENDS-ON anchor the start/end of an event to the
        # event that marks it (THYME). The faithful TimeML is IAFTER / IBEFORE,
        # NOT BEGINS / ENDS (which would wrongly assert a shared boundary plus
        # a spurious constraint on the other endpoint). EN100017 has both
        # BEGINS-ON ("started on ...") and ENDS-ON ("oedema resolved") links.
        with open(EN100017, encoding="utf-8") as f:
            result = converter.convertContent(f.read())
        self.assertTrue(result[0], result)
        tml = result[1]
        self.assertIn('relType="IBEFORE"', tml)
        self.assertIn('relType="IAFTER"', tml)
        # The old (wrong) mapping must be gone for this file.
        self.assertNotIn('relType="ENDS"', tml)
        self.assertNotIn('relType="BEGINS"', tml)

    def testConvertedFileIsValid(self):
        with open(EN100017, encoding="utf-8") as f:
            result = converter.convertContent(f.read())
        self.assertTrue(result[0])
        self.assertTrue(validator.validateContent(result[1])[0])


if __name__ == "__main__":
    unittest.main()
