import os, unittest

from pytlex_core.algorithms import TimeMLParser
from pytlex_tests.jTLEX_Data import jTLEX_Counts

"""
Error testing for TimeMLParser.py from core
This file tests each method of TimeMLParser with a set of random
.tml files + absurd input

Last updated by: iparr011
"""

problematic_bunch = {'ABC19980304.1830.1636.tml', 'APW19980213.1320.tml', 'APW19980227.0468.tml',
                     'APW19980227.0489.tml'}  # These files have extra events that is not used for instances


class TimeMLParserTestCase(unittest.TestCase):
    def test_instance_count(self):
        filepath = r"../pytlex_data/TimeBankCorpus"
        for subdir, dirs, files in os.walk(filepath):
            for filename in files:
                with open(filepath + "/" + filename) as timeMLFile:
                    instance_list = TimeMLParser.parse_instances(timeMLFile.read())
                    self.assertEqual(len(instance_list), jTLEX_Counts.jTLEX_instance_count[filename])

    def test_timex_count(self):
        filepath = r"../pytlex_data/TimeBankCorpus"
        for subdir, dirs, files in os.walk(filepath):
            for filename in files:
                with open(filepath + "/" + filename) as timeMLFile:
                    timex_list = TimeMLParser.parse_timex(timeMLFile.read())
                    self.assertEqual(len(timex_list), jTLEX_Counts.jTLEX_timex_count[filename])

    def test_link_count(self):
        filepath = r"../pytlex_data/TimeBankCorpus"
        for subdir, dirs, files in os.walk(filepath):
            for filename in files:
                with open(filepath + "/" + filename) as timeMLFile:
                    link_list = TimeMLParser.parse_links(timeMLFile.read())
                    self.assertEqual(len(link_list), jTLEX_Counts.jTLEX_link_count[filename])

    def test_event_count(self):
        # We don't have a jTLEX_events_count call yet, so for now test on
        # random .tml files whose event counts are known, and compare
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            events_list = TimeMLParser.parse_events(timeMLFile.read())
            print("Number of events:",len(events_list))
            self.assertEqual(len(events_list), 28)
        print("Filename: wsj_1014")
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_1014.tml"
        with open(filepath) as timeMLFile:
            events_list = TimeMLParser.parse_events(timeMLFile.read())
            print("Number of events:", len(events_list))
            self.assertEqual(len(events_list), 113)
        print("Filename: WSJ900813-0157")
        filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
        with open(filepath) as timeMLFile:
            events_list = TimeMLParser.parse_events(timeMLFile.read())
            print("Number of events:", len(events_list))
            self.assertEqual(len(events_list), 251)
        print("Filename: NYT19980402.0453")
        filepath = r"../pytlex_data/TimeBankCorpus/NYT19980402.0453.tml"
        with open(filepath) as timeMLFile:
            events_list = TimeMLParser.parse_events(timeMLFile.read())
            print("Number of events:", len(events_list))
            self.assertEqual(len(events_list), 50)

    def test_signal_count(self):
        # We don't have a jTLEX_signals_count call yet, so for now test on
        # random .tml files whose signal counts are known, and compare
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            signals_list = TimeMLParser.parse_signals(timeMLFile.read())
            print("Number of signals:",len(signals_list))
            self.assertEqual(len(signals_list), 5)
        print("Filename: wsj_1014")
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_1014.tml"
        with open(filepath) as timeMLFile:
            signals_list = TimeMLParser.parse_signals(timeMLFile.read())
            print("Number of signals:", len(signals_list))
            self.assertEqual(len(signals_list), 1)
        print("Filename: WSJ900813-0157")
        filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
        with open(filepath) as timeMLFile:
            signals_list = TimeMLParser.parse_signals(timeMLFile.read())
            print("Number of signals:", len(signals_list))
            self.assertEqual(len(signals_list), 0)
        print("Filename: NYT19980402.0453")
        filepath = r"../pytlex_data/TimeBankCorpus/NYT19980402.0453.tml"
        with open(filepath) as timeMLFile:
            signals_list = TimeMLParser.parse_signals(timeMLFile.read())
            print("Number of signals:", len(signals_list))
            self.assertEqual(len(signals_list), 2)

    def test_raw_text_count(self):
        # Should return a series of sentences separated by newlines. Thus the number of sentences should
        # match the number of '<s>...</s>' in the file + the number of already present newlines in the text
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            raw_text = TimeMLParser.parse_raw_text(timeMLFile.read())
            text_count = raw_text.count('\n')
            print("Number of sentences:",text_count)
            self.assertEqual(text_count, 19 + 17)
        print("Filename: wsj_1014")
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_1014.tml"
        with open(filepath) as timeMLFile:
            raw_text = TimeMLParser.parse_raw_text(timeMLFile.read())
            text_count = raw_text.count('\n')
            print("Number of sentences:", text_count)
            self.assertEqual(text_count, 26 + 3)
        print("Filename: WSJ900813-0157")
        filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
        with open(filepath) as timeMLFile:
            raw_text = TimeMLParser.parse_raw_text(timeMLFile.read())
            text_count = raw_text.count('\n')
            print("Number of sentences:", text_count)
            self.assertEqual(text_count, 57 + 6)
        print("Filename: NYT19980402.0453")
        filepath = r"../pytlex_data/TimeBankCorpus/NYT19980402.0453.tml"
        with open(filepath) as timeMLFile:
            raw_text = TimeMLParser.parse_raw_text(timeMLFile.read())
            text_count = raw_text.count('\n')
            print("Number of sentences:", text_count)
            self.assertEqual(text_count, 12 + 22)

    def test_metadata(self):
        # parse_metadata collects all metadata matches located before the text
        # It should return a list of length = number of metadata types
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            metadata = TimeMLParser.parse_metadata(timeMLFile.read())
            print("The metadata for this file is:",metadata)
            self.assertEqual(len(metadata), 1)
        print("Filename: wsj_1014")
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_1014.tml"
        with open(filepath) as timeMLFile:
            metadata = TimeMLParser.parse_metadata(timeMLFile.read())
            print("The metadata for this file is:", metadata)
            self.assertEqual(len(metadata), 8)
        print("Filename: WSJ900813-0157")
        filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
        with open(filepath) as timeMLFile:
            metadata = TimeMLParser.parse_metadata(timeMLFile.read())
            print("The metadata for this file is:", metadata)
            self.assertEqual(len(metadata), 9)
        print("Filename: NYT19980402.0453")
        filepath = r"../pytlex_data/TimeBankCorpus/NYT19980402.0453.tml"
        with open(filepath) as timeMLFile:
            metadata = TimeMLParser.parse_metadata(timeMLFile.read())
            print("The metadata for this file is:", metadata)
            self.assertEqual(len(metadata), 5)

    def test_parse(self):
        # parse compiles metadata, raw text, links, and timex+instances in a single list
        # So lets manually create a list of these elements and compare it to what parse returns
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            global metadata_supreme
            metadata_supreme = TimeMLParser.parse_metadata(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global raw_text_supreme
            raw_text_supreme = TimeMLParser.parse_raw_text(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global links_supreme
            links_supreme = TimeMLParser.parse_links(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global timex_supreme
            timex_supreme = TimeMLParser.parse_timex(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global instances_supreme
            instances_supreme = TimeMLParser.parse_instances(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global events_supreme
            events_supreme = TimeMLParser.parse_events(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global signals_supreme
            signals_supreme = TimeMLParser.parse_signals(timeMLFile.read())
        with open(filepath) as timeMLFile:
            supreme = metadata_supreme,raw_text_supreme,links_supreme,(timex_supreme+instances_supreme),signals_supreme,events_supreme
            self.assertEqual(supreme, TimeMLParser.parse(timeMLFile.read()))

    def test_parse_dict(self):
        # Similar to parse above, but instead compiles elements from the text into a dictionary
        # So lets manually create a dict and then compare to the result
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath) as timeMLFile:
            metadata_supreme = TimeMLParser.parse_metadata(timeMLFile.read())
        with open(filepath) as timeMLFile:
            raw_text_supreme = TimeMLParser.parse_raw_text(timeMLFile.read())
        with open(filepath) as timeMLFile:
            links_supreme = TimeMLParser.parse_links(timeMLFile.read())
        with open(filepath) as timeMLFile:
            timex_supreme = TimeMLParser.parse_timex(timeMLFile.read())
        with open(filepath) as timeMLFile:
            instances_supreme = TimeMLParser.parse_instances(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global events_supreme
            events_supreme = TimeMLParser.parse_events(timeMLFile.read())
        with open(filepath) as timeMLFile:
            global signals_supreme
            signals_supreme = TimeMLParser.parse_signals(timeMLFile.read())
        with open(filepath) as timeMLFile:
            supreme = {'metadata':metadata_supreme, 'raw_text':raw_text_supreme,
                       'links':links_supreme, 'timexes':timex_supreme, 'instances':instances_supreme,
                       'events':events_supreme, 'signals':signals_supreme}
            self.assertEqual(supreme, TimeMLParser.parse_dict(timeMLFile.read()))

    def test_read_file_data(self):
        # This one just reads the file to you
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"
        with open(filepath,'r') as file :
            self.assertEqual(TimeMLParser.read_file_data(filepath), file.read())
        filepath = r"../pytlex_data/TimeBankCorpus/wsj_1014.tml"
        with open(filepath, 'r') as file:
            self.assertEqual(TimeMLParser.read_file_data(filepath), file.read())
        filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
        with open(filepath, 'r') as file:
            self.assertEqual(TimeMLParser.read_file_data(filepath), file.read())
        filepath = r"../pytlex_data/TimeBankCorpus/NYT19980402.0453.tml"
        with open(filepath, 'r') as file:
            self.assertEqual(TimeMLParser.read_file_data(filepath), file.read())

    def test_absurd_input(self):
        print("Filename: ABC19980304.1830.1636")
        filepath = r"../pytlex_data/TimeBankCorpus/ABC19980304.1830.1636.tml"

        # What if given empty text? Methods should return empty lists
        self.assertEqual(TimeMLParser.parse_events(""), [])
        self.assertEqual(TimeMLParser.parse_timex(""), [])
        self.assertEqual(TimeMLParser.parse_links(""), [])
        self.assertEqual(TimeMLParser.parse_signals(""), [])
        self.assertEqual(TimeMLParser.parse_instances(""), [])
        self.assertEqual(TimeMLParser.parse_metadata(""), [])
        # Or just an empty string
        self.assertEqual(TimeMLParser.parse_raw_text(""), "")

        # What if text contains desired patterns, but they're empty?
        # Should also return empty lists
        test_text = "<EVENT></EVENT> This text is irrelevant <TIMEX3></TIMEX3>"
        self.assertEqual(TimeMLParser.parse_events(test_text), [])
        self.assertEqual(TimeMLParser.parse_timex(test_text), [])
        # What if the patterns are filled with nonsensical stuff?
        # Should return a whole load of NOTHING
        test_text2 = "<EVENT hello who is this></EVENT>"
        self.assertEqual(TimeMLParser.parse_events(test_text2), [])
        test_text3 = "<TIMEX3 Kill me.></TIMEX3>"
        self.assertEqual(TimeMLParser.parse_timex(test_text3), [])
        # What if the patterns are misannotated? Also nothing
        test_text4 = "<MAKEINSTANCE who are you people<>>"
        self.assertEqual(TimeMLParser.parse_instances(test_text4), [])
        test_text5 = "<SIGNAL> did monkeys write this stuff<SIGNAL>"
        self.assertEqual(TimeMLParser.parse_signals(test_text5), [])
        test_text6 = "<EVENT> this is the end of you, Luigi>"
        self.assertEqual(TimeMLParser.parse_events(test_text6), [])
        test_text7 = "<TLINK nice try nerd>"
        self.assertEqual(TimeMLParser.parse_links(test_text7), [])
        test_text8 = "<REDACTED> I am totally real legit metadata, trust me <REDACTED> <TEXT>"
        self.assertEqual(TimeMLParser.parse_metadata(test_text8), [])
        test_text9 = "<s> The place is not good for the imagination, and does not bring restful dreams at night. " \
                     "It must be this which keeps the foreigners away, for old Ammi Pierce has never told them of " \
                     "anything he recalls from the strange days. <s>"
        test_text10 = "\n\n\n\n\n"
        self.assertEqual(TimeMLParser.parse_raw_text(test_text10), "")
        self.assertEqual(TimeMLParser.parse_raw_text(test_text9), "")
        test_text11 = test_text2+test_text3+test_text4+test_text5+test_text6+test_text7+test_text8+test_text9
        self.assertEqual(TimeMLParser.parse(test_text11), ([], "", [], [], [], []))
        test_text12 = test_text2+test_text3+test_text4+test_text5+test_text6+test_text7+test_text8+test_text9
        result = {'metadata': [], 'raw_text': '', 'links': [], 'timexes': [], 'instances': [],
                  'events': [], 'signals': []}
        self.assertEqual(TimeMLParser.parse_dict(test_text12), result)


if __name__ == '__main__':
    unittest.main()
