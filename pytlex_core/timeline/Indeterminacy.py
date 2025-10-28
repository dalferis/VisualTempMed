from dataclasses import dataclass
from typing import Optional

"""
Represents a Trunk and Branch structure of the Timelines in a TimeML graph
This class takes a set of ordered timelines, a set of attachment links,
arranging them into a Trunk and a series of Branches.
"""


@dataclass
class Indeterminacy:
    def __init__(self,
                 shortest_timeline: dict,
                 score: float,
                 indeterminate_points: list,
                 indeterminate_sections: set,
                 indeterminate_pairs: Optional[list],
                 indeterminate_indexes: list
                 ):
        """
        :param timelines: the list of timelines created from a partitioned graph.
        :type timelines: a list of Timeline objects
        :param single_s_links: the s-links involved with a graph.
        :type single_s_links: set of s-links
        """
        self.shortest_timeline = shortest_timeline
        self.score = score
        self.indeterminate_points = indeterminate_points
        self.indeterminate_pairs = indeterminate_pairs
        self.indeterminate_sections = indeterminate_sections
        self.indeterminate_indexes = indeterminate_indexes

    def get_indeterminate_time_pairs(self) -> list:
        """
        A method for returning the indeterminant time pairs in an indeterminate timeline
        """
        if self.shortest_timeline is None:
            return []
        timeline = sum(self.shortest_timeline.values(), [])
        time_pairs = []
        for index, time_pair in enumerate(self.indeterminate_pairs):
            if self.indeterminate_pairs[index]:
                first_point = timeline[index]
                second_point = timeline[index + 1]
                time_pairs.append([first_point, second_point])
        return time_pairs

    def get_total_time_points(self) -> int:
        """
        A method for obtaining the total timepoints of all timelines in a TrunkAndBranch object
        :return: an int containing the total timepoints of all timelines in a TrunkAndBranch object
        """
        total = self.trunk.get_total_timepoints()
        for timeline in self.branches:
            total += timeline.get_total_timepoints()
        return total

    def get_node_incoming_slinks(self, node: str):
        """
        Returns all the incoming slinks for a specific node
        :return: a list of links going into a node
        """
        links = []
        for slink in self.single_s_links:
            if slink.related_to_node == node:
                links.append(slink)
        return links

    def get_node_outgoing_slinks(self, node: str):
        """
        Returns all the outgoing slinks for a specific node
        :return: a list of links going out of a node
        """
        links = []
        for slink in self.single_s_links:
            if slink.start_node == node:
                links.append(slink)
        return links

    def __repr__(self):
        ret = "Trunk: "
        ret += self.trunk.__repr__()
        if self.branches is not None:
            for branch in self.branches:
                ret += "\nBranch: " + branch.__repr__()
        return ret
