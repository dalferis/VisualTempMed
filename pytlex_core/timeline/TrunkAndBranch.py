from dataclasses import dataclass
from typing import Optional

"""
Represents a Trunk and Branch structure of the Timelines in a TimeML graph
This class takes a set of ordered timelines, a set of attachment links,
arranging them into a Trunk and a series of Branches.
"""


@dataclass
class TrunkAndBranch:
    def __init__(self,
                 timelines: Optional[list] = None,
                 single_s_links: Optional[list] = None):
        """
        :param timelines: the list of timelines created from a partitioned graph.
        :type timelines: a list of Timeline objects
        :param single_s_links: the s-links involved with a graph.
        :type single_s_links: set of s-links
        """
        self.trunk = None
        self.branches = []
        self.single_s_links = None
        self.attachment_points = None

        if not timelines:
            if timelines is not None and len(timelines) != 0:
                raise Exception("Error, Timeline must be passed in as a Dict")
            else:
                self.trunk = None
                self.branches = None
                self.single_s_links = None
                self.attachment_points = None
        else:
            self.trunk = max(timelines, key=len)  # Finds the largest timeline to set as trunk

            for timeline in timelines:
                if timeline != self.trunk:
                    self.branches.append(timeline)  # Adds all other timelines to branches
            self.single_s_links = single_s_links
            if single_s_links is not None:
                self.attachment_points = []
                for link in single_s_links:  # Initializes attachment points if there are S-Links
                    self.attachment_points.append(link.start_node + "->" + link.related_to_node)

    def get_total_timelines(self) -> int:
        """
        A method for returning the number of timelines in a TrunkAndBranch object
        :return: an int containing the number of timelines in a TrunkAndBranch object
        """
        return len(self.branches) + 1

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
