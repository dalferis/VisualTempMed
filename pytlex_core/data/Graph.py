from typing import Union, Optional

from pytlex_core.algorithms import TimeMLParser
from pytlex_core.data.Event import Event
from pytlex_core.data.Instance import Instance
from pytlex_core.data.Link import Link
from pytlex_core.data.Signal import Signal
from pytlex_core.data.TimeX import TimeX


class Graph:
    def __init__(self,
                 nodes: Optional[set[Union[TimeX, Instance]]] = None,
                 links: Optional[set[Link]] = None,
                 events: Optional[set[Event]] = None,
                 signals: Optional[set[Signal]] = None,
                 filepath: Optional[str] = None,
                 time_ml_string: Optional[str] = None
                 ):
        """
        :param nodes: the nodes to be placed in an empty graph.
        :type nodes: set of TimeXs and Instances
        :param links: the links to be placed in an empty graph.
        :type links: set of Links
        :param str filepath: the path to a TimeML annotated file to be parsed and analyzed.
        :param str time_ml_string: a TimeML annotated string to be analyzed.
        """

        self.nodes = {}
        self.links = {}
        self.signals = {}
        self.events = {}
        self.raw_text = None
        self.type = "Overview"
        self.consistency = None
        self.total_time_points = 0

        if not (nodes or links or filepath or time_ml_string):
            pass

        elif nodes is not None:

            if "e" in nodes:
                self.events = {event.get_id_str(): event for event in events}
                self.nodes = {node.get_id_str(): node for node in nodes}
            else:
                self.nodes = {node.get_id_str(): node for node in nodes}

            self.links = {link.get_id_str(): link for link in links}
            if signals is not None:
                self.signals = {signal.get_id_str(): signal for signal in signals}

        elif (filepath is not None) or (time_ml_string is not None):
            if filepath:
                with open(filepath) as file:
                    self.time_ml_data = file.read()
            elif time_ml_string:
                self.time_ml_data = time_ml_string

            self.metadata, self.raw_text, links, nodes, signals, events = TimeMLParser.parse(self.time_ml_data)

            if len(nodes) == 0:
                raise Exception("No Nodes found in Text")

            self.events = {event.get_id_str(): event for event in events}
            self.links = {link.get_id_str(): link for link in links}
            self.nodes = {node.get_id_str(): node for node in nodes}
            if signals is not None:
                self.signals = {signal.get_id_str(): signal for signal in signals}

        else:
            raise Exception("Must supply either a TimeML Annotated File or a TimeML annotated string")

    def to_json(self):
        ret = "{\"nodeIds\": ["
        for node in self.nodes.keys():
            ret += "\"" + node + "\", "

        ret = ret[:-2] + "], "

        ret += "\"links\": ["
        if not self.links:
            ret += ", "
        for link in self.links.values():
            ret += "{\"id\": \"" + link.get_id_str() + "\", "
            ret += "\"from\": \"" + link.start_node + "\", "
            ret += "\"type\": \"" + link.rel_type + "\", "
            ret += "\"to\": \"" + link.related_to_node + "\"}, "

        ret = ret[:-2] + "], "

        ret += "\"events\": ["
        if not self.events:
            ret += ", "
        for event in self.events.values():
            ret += event.to_json() + ", "

        ret = ret[:-2] + "]}"
        return ret

    def __repr__(self):
        ret = "Nodes: "
        for node in self.nodes.values():
            ret += node.to_json()
            ret += ", "

        ret = ret[:-2] + "\n"

        ret += "Links: "
        for link in self.links.values():
            ret += link.to_json()
            ret += ", "

        ret = ret[:-2] + "\n "
        return ret

    def to_string(self):

        ret = "Nodes: "
        for node in self.nodes.values():
            ret += node.to_json()
            ret += ", "

        ret = ret[:-2] + "\n"

        ret += "Links: "
        for link in self.links.values():
            ret += link.to_json()
            ret += ", "

        ret = ret[:-2] + "\n "
        return ret
