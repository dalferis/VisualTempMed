from dataclasses import dataclass
from typing import Optional

from pytlex_core.algorithms import Z3_tcsp_solver
from pytlex_core.data.Graph import Graph

"""
Represents a Timeline of a TimeML graph, which is an ordered list of the
events extracted from a TimeML Graph. TimeML annotations are converted into a
collection of main and subordinated timelines arranged into a
trunk-and-branch style structure. This class takes an ordered timeline, a set
of attachment links, arranging them into a Timeline.
"""


def find_timeline(partition: Graph):
    """
    A method for taking in graphs/partitions and returning a dict that contains
    a timeline for said graph/partition.

    :param partition: the partition the timeline is being found for
    :type partition: a Graph object
    :return: a dict solution that can be turned into a timeline object
    """
    timeline = Z3_tcsp_solver.solve(partition)
    partition.consistency = True if timeline is not None else False
    return timeline


@dataclass
class Timeline:
    def __init__(self,
                 timeline: Optional[dict] = None):
        """
        :param timeline: The solved timeline of a Graph.
        :type timeline: a dictionary
        """
        self.timeline = {}

        if not timeline:
            raise Exception("Error, Timeline must be passed in as a Dict")
        else:
            self.timeline = timeline

    def get_total_timepoints(self) -> int:
        """
        Finds the amount of timepoints in a timeline
        :return: an int containing the # of timepoints
        """
        time_points = 0
        for time in self.timeline.values():
            time_points += len(time)
        return time_points

    def get_timepoints(self, section: int):
        """
        :param section: an int for the section the timepoints are located in
        :return: the timepoints at that section
        """
        return self.timeline[str(section)]

    def get_first_point(self):
        """
        A method for obtaining the timepoints at the beginning of a timeline
        :return: the timepoints at the first section of a timeline
        """
        return self.timeline['1']

    def get_last_point(self):
        """
        A method for obtaining the timepoints at the end of a timeline
        :return: the timepoints at the last section of a timeline
        """
        return self.timeline[str(len(self.timeline))]

    def get_timeline_length(self):
        """
        A method for obtaining the length of a timeline, specifically its sections
        :return: an int with the length of the timeline
        """
        return len(self.timeline)

    def to_json(self):
        """
        Outputs the Timeline in JSON format
        :return: a JSON Formatted String for the Timeline
        """
        ret = "["

        for timepoint, nodes in self.timeline.items():
            for node in nodes:
                node_values = node.split("_")
                node_id = node_values[0]
                node_boundary = node_values[1]
                ret += "{\"id\":\"" + node_id + "\","
                if "plus" in node_boundary:
                    ret += "\"eventBoundary\":\"+\","
                else:
                    ret += "\"eventBoundary\":\"-\","
                ret += "\"position\":\"" + timepoint + "\"},"

        ret = ret[:-1] + "]"
        return ret

    def __repr__(self):
        return str(self.timeline)

    def __len__(self):
        return self.get_timeline_length()

    def __eq__(self, other):
        return self.timeline == other.timeline
