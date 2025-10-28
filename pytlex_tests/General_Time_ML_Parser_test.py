# Written by: vfern124
# Last updated: vfern124

import os
import re
from time import perf_counter
from pytlex_core.algorithms import TimeMLParser


# This tester checks each file using counting, does not check if the contents of each are correct
# If having running issues, do ALT-SHIFT-F10, then run 'General_Time_ML_Parser_test'


def test_events(file, printing=False) -> bool:
    count_events_pattern = re.compile(r'<EVENT')
    count_events = count_events_pattern.findall(file)
    events = TimeMLParser.parse_events(file)
    if printing:
        print('Caught all events?\t' + str(len(count_events) == len(events)))
    return len(count_events) == len(events)


def test_timex(file, printing=False) -> bool:
    count_timexes_pattern = re.compile(r'<TIMEX3')
    count_timexes = count_timexes_pattern.findall(file)
    timexes = TimeMLParser.parse_timex(file)
    if printing:
        print('Caught all timexes?\t' + str(len(count_timexes) == len(timexes)))
    return len(count_timexes) == len(timexes)


def test_signal(file, printing=False) -> bool:
    count_signals_pattern = re.compile(r'<SIGNAL')
    count_signals = count_signals_pattern.findall(file)
    signals = TimeMLParser.parse_signals(file)
    if printing:
        print('Caught all signals?\t' + str(len(count_signals) == len(signals)))
    return len(count_signals) == len(signals)


def test_instance(file, printing=False) -> bool:
    count_instances_pattern = re.compile(r'<MAKEINSTANCE ')
    count_instances = count_instances_pattern.findall(file)
    instances = TimeMLParser.parse_instances(file)
    if printing:
        print('Caught all instances?\t' + str(len(count_instances) == len(instances)))
    return len(count_instances) == len(instances)


def test_link(file, printing=False) -> bool:
    count_links_pattern = re.compile(r'<([AST]LINK) ')
    count_links = count_links_pattern.findall(file)
    links = TimeMLParser.parse_links(file)
    if printing:
        print('Caught all links?\t' + str(len(count_links) == len(links)))
    return len(count_links) == len(links)


def run_test(name, file, printing=False):
    passing = True
    failed = []
    if printing:
        print('Attempting file ' + name)
        print('___________________________')

    if not test_events(file, printing):
        passing = False
        failed += ['EVENT']

    if not test_timex(file, printing):
        passing = False
        failed += ['TIMEX3']

    if not test_signal(file, printing):
        passing = False
        failed += ['SIGNAL']

    if not test_instance(file, printing):
        passing = False
        failed += ['INSTANCE']

    if not test_link(file, printing):
        passing = False
        failed += ['LINK']

    if printing:
        print()

    return passing, failed


if __name__ == '__main__':
    list_of_complex_timex3 = ["AP900815-0044.tml", "APW19980227.0487.tml", "APW19980227.0489.tml",
                              "APW19980322.0749.tml", "wsj_0570.tml", "wsj_0585.tml", "wsj_0637.tml", "wsj_0768.tml"]
    filepath = '../pytlex_data/TimeBankCorpus'
    flagged = []
    start_time = perf_counter()
    for subdir, dirs, files in os.walk(filepath):
        for filename in files:
            with open(filepath + "/" + filename) as file:
                check, failed_tests = run_test(filename, file.read(), False)
                if not check:
                    flagged += [[filename, failed_tests]]

    print('Flagged files: ' + str(flagged))
    print(f'Test time: {perf_counter() - start_time:0.4f} seconds')
    print()

    for f in flagged:
        with open(filepath + "/" + f[0]) as file:
            string = file.read()
            print('Testing ' + f[0])
            for test in f[1]:
                if test == 'EVENT':
                    test_events(string, True)
                    events = TimeMLParser.parse_events(string)
                    for e in events:
                        print(e.get_id_str(), end=', ')

                elif test == 'TIMEX3':
                    test_timex(string, True)
                    timexes = TimeMLParser.parse_timex(string)
                    for t in timexes:
                        print(t.get_id_str(), end=', ')
                    print()

                elif test == 'SIGNAL':
                    test_signal(string, True)
                    signals = TimeMLParser.parse_signals(string)
                    for s in signals:
                        print(s.get_id_str())

                elif test == 'INSTANCE':
                    test_instance(string, True)
                    instances = TimeMLParser.parse_instances(string)
                    for i in instances:
                        print(i.get_id_str())

                elif test == 'LINK':
                    test_link(string, True)
                    links = TimeMLParser.parse_links(string)
                    for l in links:
                        print(l.get_id_str())
            print()
