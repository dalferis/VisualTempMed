from typing import Any, List
from pytlex_core.data.TimeX import TimeX
from pytlex_core.data import Link
import datetime

"""
Main function of the Connectivity_Increaser script. 
@:arg output_as_dict, result from the partitioner in 
                    in dictionary form
@:arg number_of_links in the original TimeML graph
"""

def connect_partitions(output_as_dict, number_of_links) -> Link:
    """
    create a dictionary to store the disconnected partitions
    anchor is defined as the partition that holds the DCT
    connectivity candidates are other partitions that have
    time expressions that could be connected with the dct
    """
    disconnected_partitions = {"anchor": [], "connectivity_candidates": []}

    """
    if a partition is the main partition and has the DCT, then it is an anchor
    if the partition has the DCT but it is not a main partition, it is also the anchor
    other partitions with time expressions are candidates for connectivity
    """
    for partition in (output_as_dict["main_graphs"]+ output_as_dict["subordination_graphs"]):
        if partition.type == "main_graph" and get_dct(partition):
            disconnected_partitions["anchor"] = partition
        elif get_dct(partition):
            disconnected_partitions["anchor"] = partition
        elif has_time_expressions(partition.nodes):
            disconnected_partitions["connectivity_candidates"].append(partition)

    #add to the dictionary an entry "suggested links", where
    output_as_dict["suggested_links"] = try_suggest_link(disconnected_partitions, number_of_links)

"""
@:arg set of nodes in a partition
@:returns true if one of the nodes is a valid time expression (and if it doesnt include a
4-digit year value for a DATE type), false otherwise

NOTE (VisualTempoMed PFG patch): partition.nodes is a dict {id: node}; the
original code iterated the dict directly, yielding keys (strings). The
str.tID lookups raised AttributeError that was silently swallowed below, so
the function always returned False. Now we iterate values() when given a
dict and fall back to plain iteration otherwise (preserves backwards-compat
for callers passing a list/set of nodes).
"""
def has_time_expressions(nodes):
    iterable = nodes.values() if isinstance(nodes, dict) else nodes
    for node in iterable:
        try:
            # The ID of a valid time expression must be a positive integer
            # And it must have a value to analyze
            if isinstance(node.tID,int) and (node.tID >= 0) and (node.value is not None) :
                if node.type == "DATE" and len(node.value) == 4 and node.value[3]=="X" :
                    return False
                else :
                    return True  # TimeX with a 4-digit year value ending in X should be ignored
        except AttributeError:
            pass
    return False


"""
@:arg the dictionary of disconnected partitions
@:arg the number of links in the original timeML graph
@:returns the list of suggested links for this partition
"""
def try_suggest_link(disconnected_partitions, number_of_links):
    #get the dct from the anchor
    dct = get_dct(disconnected_partitions["anchor"])
    suggested_links = []

    #graph cannot have negative number of links
    if number_of_links < 0:
        err = "ERROR: Graph cannot have a negative number of links"
        raise RuntimeError(err)
    #it also cannot be less than the number of links in all partitions combined
    count = 0
    for partition in disconnected_partitions["connectivity_candidates"]:
        count += len(partition.links)
    if number_of_links < count :
        err = "ERROR: Number of links from partitions exceed number of links from graph"
        raise RuntimeError(err)

    #if the dct exists
    if dct:
        try:
            #go through the candidates
            for partition in disconnected_partitions["connectivity_candidates"]:
                #ge the time expressions for this partition
                time_expressions = get_timexs(partition.nodes)
                #suggest a link between the dct and any time expressions
                suggestion = suggest_link(dct, time_expressions, number_of_links)
                #if there was a suggestion, add it to the list
                if suggestion is not None:
                    suggested_links.append(suggestion)
            #return the list
            return suggested_links
        except KeyError:
            #if there are no connectivity candidates, return an empty list
            return suggested_links

"""
@:arg the partition that contains the dct
@:returns the DCT

NOTE (VisualTempoMed PFG patch): same iteration fix as has_time_expressions
above. partition.nodes is a dict; iterating gives keys, so node.documentFunction
raised AttributeError and the function always returned None.
"""
def get_dct(partition_with_dct) -> TimeX:
    try:
        nodes = partition_with_dct.nodes
        iterable = nodes.values() if isinstance(nodes, dict) else nodes
        for node in iterable:
            try:
                #a DCT is a node that contains "CREATION_TIME" or "PUBLICATION_TIME" as their function value
                if node.documentFunction == "CREATION_TIME" or  node.documentFunction == "PUBLICATION_TIME":
                    return node
            except AttributeError:
                pass
    except AttributeError:
        return None

"""
@:arg a set of nodes
@:returns valid time expressions that fulfill a number of conditions

NOTE (VisualTempoMed PFG patch): same iteration fix as has_time_expressions
above. partition.nodes is a dict; iterating gives keys, so the whole
function silently returned an empty list.
"""
def get_timexs(nodes: Any):
    timexs = []
    iterable = nodes.values() if isinstance(nodes, dict) else nodes
    for node in iterable:
        try:
            if isinstance(node.tID,int) and (node.tID >= 0) and (node.value is not None) :
                if node.type == "DATE" and len(node.value)<4 :
                    err = "TimeX value for t"+str(node.tID)+" is incorrect. Expected at least 4 digits"
                    raise RuntimeError(err)
                if node.type not in {"DURATION", "SET"} and \
                        node.value not in {"PAST_REF", "PRESENT_REF", "FUTURE_REF", "PXY"}:
                    # Check for invalid values when type == DATE or TIME. For these types, 2nd digit of
                    # value must be always an integer (except when DATE starts value with "XXXX")
                    if "XXXX" not in node.value :
                        try:
                            if isinstance(int(node.value[1]), int):
                                pass
                        except ValueError:
                            err = "Invalid value for DATE or TIME type node"
                            raise RuntimeError(err)
                        if node.type == "DATE" and len(node.value) == 4 and node.value[3] == "X":
                            pass  # 4-digit years that end with X (i.e. 198X, etc) should be ignored
                        else :
                            timexs.append(node)
                    else :
                        timexs.append(node)
        except AttributeError:
            pass
    return timexs

"""
@:arg dct, the DCT of the graph
@:arg timexs, the list of time expressions from the candidate partition
@:arg number_of_links, the number of links in the graph
@:returns a link that will connect the DCT with another time expression
"""
def suggest_link(dct: TimeX, timexs: List[TimeX], number_of_links):
    """
    In each step of the algorithm, take the value for month, date and day
    of one of the time expressions and compare with the respective values
    of the dct. The link tempral relation will be BEFORE, AFTER or INCLUDES
    accordingly
    In cases where dct == None or timexs is empty, return None
    """
    if timexs and (dct is not None):
        # DCT should include value formatted as "XXXX-XX-XX", raise exception otherwise
        if (dct.value is None) or (len(dct.value) < 10):
            err = "Invalid value for DCT, expected DATE formatted as XXXX-XX-XX"
            raise ValueError(err)
        # Graph cannot have negative number of links
        if number_of_links < 0:
            err = "ERROR: Graph cannot have a negative number of links"
            raise RuntimeError(err)
        dct_year = int(dct.value[0:4])
        dct_month = int(dct.value[5:7])
        dct_day = int(dct.value[8:10])
        for time_expression in timexs:
            time_value = time_expression.value
            # Given time expressions should not be None
            if time_value is None :
                err = "Invalid value for TimeX, expected DATE but was given None"
                raise ValueError(err)
            if 'X' not in time_value[0: 4]:
                time_expression_year = int(time_value[0: 4])
            else:
                continue

            if time_expression_year < dct_year:
                number_of_links += 1
                return Link.Link(number_of_links, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
            elif time_expression_year > dct_year:
                number_of_links += 1
                return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
            else:
                time_expression_month = time_value[5:7]
                if len({"X", "S", "U", "F", "A", "P", "E"}.intersection(set(time_value[5:]))) != 0:
                    number_of_links += 1
                    return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                elif time_expression_month == "":
                    number_of_links += 1
                    return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                elif "Q" in time_expression_month:
                    dct_month_as_quarter = convert_month_to_quarter(dct_month)
                    if time_expression_month < dct_month_as_quarter:
                        return Link.Link(number_of_links + 1, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
                    elif time_expression_month > dct_month_as_quarter:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
                    else:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                elif "H" in time_expression_month:
                    dct_month_as_half = convert_month_to_half(dct_month)
                    if time_expression_month < dct_month_as_half:
                        return Link.Link(number_of_links + 1, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
                    elif time_expression_month > dct_month_as_half:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
                    else:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                elif "W" in time_expression_month:
                    if time_value[5:8] != time_expression_month:
                        time_expression_month = time_value[5:8]
                    _, week, _ = datetime.date(dct_year,dct_month,dct_day).isocalendar()
                    dct_as_week = "W" +str(week)
                    if time_expression_month < dct_as_week:
                        return Link.Link(number_of_links + 1, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
                    elif time_expression_month > dct_as_week:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
                    else:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                else:
                    if int(time_expression_month) < dct_month:
                        return Link.Link(number_of_links + 1, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
                    elif int(time_expression_month) > dct_month:
                        number_of_links += 1
                        return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
                    else:
                        time_expression_day = time_value[8:10]
                        if time_expression_day == "" or len({"X", "S", "U", "F", "A", "P", "E"}.intersection(set(time_value[8:]))) != 0:
                            number_of_links += 1
                            return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
                        else:
                            if int(time_expression_day) < dct_day:
                                return Link.Link(number_of_links + 1, "TLINK", "BEFORE", time_expression.get_id_str(), dct.get_id_str())
                            elif int(time_expression_day) > dct_day:
                                number_of_links += 1
                                return Link.Link(number_of_links, "TLINK", "AFTER", time_expression.get_id_str(), dct.get_id_str())
                            else:
                                number_of_links += 1
                                return Link.Link(number_of_links, "TLINK", "INCLUDES", time_expression.get_id_str(), dct.get_id_str())
    return None

"""
@:arg an integer value representing a valid month
@returns the string representation of that integer as a quarter of the year 
"""
def convert_month_to_quarter(month):
    if month in {1,2,3}:
        return "Q1"
    elif month in {4,5,6}:
        return "Q2"
    elif month in {7,8,9}:
        return "Q3"
    elif month in {10,11,12}:
        return "Q4"
    else :
        err = "Invalid value for month, expected integer between 1 and 12"
        raise ValueError(err)

"""
@:arg an integer value representing a valid month
@returns the string representation of that integer as a half of the year 
"""
def convert_month_to_half(month):
    if month in {1,2,3,4,5,6}:
        return "H1"
    elif month in {7,8,9,10,11,12}:
        return "H2"
    else :
        err = "Invalid value for month, expected integer between 1 and 12"
        raise ValueError(err)
