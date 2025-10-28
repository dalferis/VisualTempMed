"""
Error testing for Connectivity_Increaser.py from core
This file tests each method of Connectivity_Increaser with a number of .tml files
and checks for absurd input

Created by: iparr011
"""

import unittest

from pytlex_core.data.Graph import Graph
from pytlex_core.algorithms.Partitioner import partition_graph
from pytlex_core.algorithms import Connectivity_Increaser
from pytlex_core.data.TimeX import TimeX
from pytlex_tests import Testing_utilities as test_ut


class ConnectivityIncreaserTest(unittest.TestCase):
    error_message = 'Erroneous or unexpected output'

    # First let's use a short simple .tml file
    def test_connectivity_increaser_wsj_1073(self):
        print()
        graph = test_ut.wsj_1073()
        partitions = partition_graph(graph)
        links = graph.links
        print("Filename: wsj_1073")

        # Test connect_partitions
        result = Connectivity_Increaser.connect_partitions(partitions, len(links))
        self.assertEqual(result,None)

        # Test has_time_expressions
        print()
        result = list()
        count = 0
        for partition in (partitions["main_graphs"]+ partitions["subordination_graphs"]) :
            if Connectivity_Increaser.has_time_expressions(partition.nodes) :
                count += 1
            result.append(Connectivity_Increaser.has_time_expressions(partition.nodes))
            print("For this partition, the nodes are:")
            for node in partition.nodes :
                print(node)
            print("So far,",result.count(True),"partition(s) include time expressions")
        print("For this partitioned graph,",count,"partition(s) total include time expressions")
        self.assertEqual(result.count(True),count)

        # Test get_dct
        print()
        result = list()
        count = 0
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            dct = Connectivity_Increaser.get_dct(partition)
            if dct is not None :
                result.append(Connectivity_Increaser.get_dct(partition))
                count += 1
        if count > 0 :
            self.assertTrue(len(result) == 1)  # Note there can be only 1 dct max per graph
            dct = result[0]
            print("The DCT for this graph is:")
            print(dct)
        else :
            self.assertTrue(len(result) == 0)
            print("This graph has no DCT")

        # Test get_timexs
        print()
        result = 0
        timexs_list = list()
        timexs_list_partition = list()
        for partition in (partitions["main_graphs"]+ partitions["subordination_graphs"]) :
            node = Connectivity_Increaser.get_timexs(partition.nodes)
            timexs_list_partition.append(node)
            if node:
                for link in node :
                    timexs_list.append(link)
                    result += 1
        print("The time expressions for this graph are:")
        for timex in timexs_list :
            print(timex)
        print("Number of time expressions in graph =",result)
        if len(timexs_list) > 0 :
            self.assertEqual(result,len(timexs_list))
        else :
            self.assertEqual(result,0)

        # Test suggest_link
        print()
        print("DCT for this graph =",dct)
        print("Number of links in graph =",len(links))
        i = 0
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            is_this_anchor = False
            print("List of TimeX for partition",i+1,"=",timexs_list_partition[i])
            result = Connectivity_Increaser.suggest_link(dct, timexs_list_partition[i], len(links))
            for timex in timexs_list_partition[i] :
                if timex == dct :
                    is_this_anchor = True
                    break
            if timexs_list_partition[i] and (dct is not None) and (len(links) > 0) and (not is_this_anchor) :
                print("Suggested link for this partition =",result)
                self.assertTrue(result)
            elif is_this_anchor :
                print("This partition is an anchor and thus not a connectivity candidate")
            else :
                print("There are no suggested links for this partition")
                self.assertEqual(result,None)
            i += 1
        # CHANGE suggest_link TO HANDLE "None" DCTs

        # Test try_suggest_link
        print()
        result = list()
        if count > 0:
            if partitions["suggested_links"]:
                print("The suggested links for this graph are:")
                for link in partitions["suggested_links"]:
                    print(link)
                    result.append(link.start_node.tID)
                self.assertTrue(len(result) > 0)
            else:
                print("While this graph has a DCT, there are no connectivity candidates, thus no suggested links")
                self.assertTrue(len(result) == 0)
        else:
            print("As there is no DCT, there are no suggested links")
            self.assertTrue(len(result) == 0)

        # Test convert_month_to_quarter
        print()
        for month in range(1,13) :
            result = Connectivity_Increaser.convert_month_to_quarter(month)
            print("Month",month,"corresponds to quarter",result)
            if month in {1,2,3} :
                self.assertEqual(result,"Q1")
            if month in {4,5,6} :
                self.assertEqual(result,"Q2")
            if month in {7,8,9} :
                self.assertEqual(result,"Q3")
            if month in {10,11,12} :
                self.assertEqual(result,"Q4")

        # Test convert_month_to_half
        print()
        for month in range(1, 13):
            result = Connectivity_Increaser.convert_month_to_half(month)
            print("Month", month, "corresponds to half", result)
            if month in {1,2,3,4,5,6} :
                self.assertEqual(result,"H1")
            if month in {7,8,9,10,11,12} :
                self.assertEqual(result,"H2")

    # Now let's test with a larger .tml file
    # This one also includes a DATE TimeX with a 4-digit year ending in X for a value
    # which we need to test for as well
    def test_connectivity_increaser_wsj_1014(self):
        print()
        graph = Graph(filepath=r"../pytlex_data/TimeBankCorpus/wsj_1014.tml")
        partitions = partition_graph(graph)
        links = graph.links
        print("Filename: wsj_1014")

        # Test connect_partitions
        result = Connectivity_Increaser.connect_partitions(partitions, len(links))
        self.assertEqual(result,None)

        # Test that TimeX with a 4-digit year value ending in X are detected
        print("The following nodes will be ignored by connectivity_increaser:")
        count = 0
        for partition in (partitions["main_graphs"]+ partitions["subordination_graphs"]) :
            for node in partition.nodes :
                try:
                    if node.tID is not None \
                            and node.type == "DATE" and len(node.value) == 4 and node.value[3]=="X" :
                        count += 1
                        print(node)
                except AttributeError:
                    pass
        if count == 0 :
            print("None of them!")

        # Test has_time_expressions
        print()
        result = list()
        count = 0
        for partition in (partitions["main_graphs"]+ partitions["subordination_graphs"]) :
            if Connectivity_Increaser.has_time_expressions(partition.nodes) :
                count += 1
            result.append(Connectivity_Increaser.has_time_expressions(partition.nodes))
            print("For this partition, the nodes are:")
            for node in partition.nodes :
                print(node)
            print("So far,",result.count(True),"partition(s) include time expressions")
        print("For this partitioned graph,",count,"partition(s) total include time expressions")
        self.assertEqual(result.count(True),count)

        # Test get_dct
        print()
        result = list()
        count = 0
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            dct = Connectivity_Increaser.get_dct(partition)
            if dct is not None :
                result.append(Connectivity_Increaser.get_dct(partition))
                count += 1
        if count > 0 :
            self.assertTrue(len(result) == 1)  # Note there can be only 1 dct max per graph
            dct = result[0]
            print("The DCT for this graph is:")
            print(dct)
        else :
            self.assertTrue(len(result) == 0)
            print("This graph has no DCT")

        # Test get_timexs
        print()
        result = 0
        timexs_list = list()
        timexs_list_partition = list()
        for partition in (partitions["main_graphs"]+ partitions["subordination_graphs"]) :
            node = Connectivity_Increaser.get_timexs(partition.nodes)
            timexs_list_partition.append(node)
            if node:
                for link in node :
                    timexs_list.append(link)
                    result += 1
        print("The time expressions for this graph are:")
        for timex in timexs_list :
            print(timex)
        print("Number of time expressions in graph =",result)
        if len(timexs_list) > 0 :
            self.assertEqual(result,len(timexs_list))
        else :
            self.assertEqual(result,0)

        # Test suggest_link
        print()
        print("DCT for this graph =",dct)
        print("Number of links in graph =",len(links))
        i = 0
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            is_this_anchor = False
            print("List of TimeX for partition",i+1,"=",timexs_list_partition[i])
            result = Connectivity_Increaser.suggest_link(dct, timexs_list_partition[i], len(links))
            print(result)
            for timex in timexs_list_partition[i] :
                if timex == dct :
                    is_this_anchor = True
                    break
            if timexs_list_partition[i] and (dct is not None) and (len(links) > 0) and (not is_this_anchor) :
                print("Suggested link for this partition =",result)
                self.assertTrue(result)
            elif is_this_anchor :
                print("This partition is an anchor and thus not a connectivity candidate")
            else :
                print("There are no suggested links for this partition")
                self.assertEqual(result,None)
            i += 1

        # Test try_suggest_link
        print()
        result = list()
        if count > 0:
            if partitions["suggested_links"]:
                print("The suggested links for this graph are:")
                for link in partitions["suggested_links"]:
                    print(link)
                    result.append(link.start_node.tID)
                self.assertTrue(len(result) > 0)
            else:
                print("While this graph has a DCT, there are no connectivity candidates, thus no suggested links")
                self.assertTrue(len(result) == 0)
        else:
            print("As there is no DCT, there are no suggested links")
            self.assertTrue(len(result) == 0)

    # Testing for absurd and W a C k Y ! ! ! input
    # also some tests to make sure select TimeX are being properly ignored
    def test_connectivity_increaser_extras(self):

        # Get dummy test file
        print()
        graph = test_ut.wsj_1073()
        partitions = partition_graph(graph)
        links = graph.links
        # Create a time expression without a value, for testing
        timexes = [TimeX(1, None, True, "howdy", "DATE", "BEFORE", "NONE",
                          None, None, None, None, None)]

        # Test has_time_expressions for absurd input
        print()
        # A TimeX tID should not be empty, therefore has_time_expressions should
        # not accept a TimeX with a missing tID
        # First grab some TimeX and manually set their tIDs to ""
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            for node in partition.nodes :
                try:
                    if node.tID is not None :
                        node.tID = ""
                except AttributeError:
                    pass
            # Then make sure they are not identified as valid TimeX
            self.assertEqual(Connectivity_Increaser.has_time_expressions(partition.nodes), False)
        # It should also not be negative, so check for that too
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            for node in partition.nodes:
                try:
                    if node.tID is not None:
                        node.tID = -1
                except AttributeError:
                    pass
            self.assertEqual(Connectivity_Increaser.has_time_expressions(partition.nodes), False)
        # What if there is no value? Shouldn't be valid either
        self.assertEqual(Connectivity_Increaser.has_time_expressions(timexes), False)

        # Testing try_suggest_link for absurd input
        disconnected_partitions = {"anchor": [], "connectivity_candidates": []}
        number_of_links = -1
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.try_suggest_link(disconnected_partitions, number_of_links)
        # What if number of links from graph is less than number of links from
        # all partitions combined?
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            disconnected_partitions["connectivity_candidates"].append(partition)
        number_of_links = 1
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.try_suggest_link(disconnected_partitions, number_of_links)

        # Test get_dct for absurd input
        for partition in (partitions["main_graphs"] + partitions["subordination_graphs"]):
            partition.nodes = set()
            # What if the partition (somehow) has no nodes? Should return None
            self.assertEqual(Connectivity_Increaser.get_dct(partition), None)

        # Test get_timexs for absurd input, plus other stuff
        # If type == DATE and value is less than 4 digits, should raise an exception
        timexes = [TimeX(1, "193", True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.get_timexs(timexes)
        # If node has no value, should be ignored
        timexes = [TimeX(1, None, True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        self.assertEqual(Connectivity_Increaser.get_timexs(timexes), [])
        # If type == DATE and node has 4-digits and ends with X, node should be ignored
        timexes = [TimeX(1, "198X", True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        self.assertEqual(Connectivity_Increaser.get_timexs(timexes), [])
        # If type == DATE or TIME and value is invalid, should raise an exception
        timexes = [TimeX(1, "ahskhakj", True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.get_timexs(timexes)
        # What if value is invalid but has exactly 4 digits and ends with X?
        # Should raise an exception, not just be ignored
        timexes = [TimeX(1, "ahsX", True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.get_timexs(timexes)

        # Testing suggest_link for absurd input
        timexes = [TimeX(1, "1989", True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        number_of_links = 2
        # What if dct has no value, or is invalid? Should raise an exception
        dct = TimeX(1, None, True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.suggest_link(dct, timexes, number_of_links)
        dct = TimeX(1, "1998", True, "howdy", "DATE", "BEFORE", "NONE",
                    None, None, None, None, None)
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.suggest_link(dct, timexes, number_of_links)
        # What if number of links is invalid? Also exception
        dct = TimeX(1, "1998-10-11", True, "howdy", "DATE", "BEFORE", "NONE",
                    None, None, None, None, None)
        number_of_links = -1
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.suggest_link(dct, timexes, number_of_links)
        # What if any of the given TimeX has no value? Exception it up
        number_of_links = 2
        timexes = [TimeX(1, None, True, "howdy", "DATE", "BEFORE", "NONE",
                         None, None, None, None, None)]
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.suggest_link(dct, timexes, number_of_links)

        # Test convert_month_to_quarter and convert_month_to_half for absurd input
        # What if month number is invalid? Or not an int? Should raise exception
        wacky_month = 13
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.convert_month_to_quarter(wacky_month)
            Connectivity_Increaser.convert_month_to_half(wacky_month)
        wacky_month = 0
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.convert_month_to_quarter(wacky_month)
            Connectivity_Increaser.convert_month_to_half(wacky_month)
        wacky_month = "December"
        with self.assertRaises(Exception):  # Should return true
            Connectivity_Increaser.convert_month_to_quarter(wacky_month)
            Connectivity_Increaser.convert_month_to_half(wacky_month)

if __name__ == '__main__':
    unittest.main()
