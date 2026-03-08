from math import e, floor
from re import I
import sys
from turtle import window_width
from PySide6.QtGui import QColor
import networkx as nx
import matplotlib.pyplot as plt
import utils
from pytlex_core.data import Event, Graph, Instance, TimeX, Signal, Link
from pytlex_core.algorithms import TLEX, TimeMLParser
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsPathItem
)
from PySide6.QtCore import Qt
import graphView as gv
import mainWindow as mw


window_width = 1024
window_height = 1024
max_columns = 15
horizontal_distance = 150
vertical_distance = 80

def getScene(graph, tlex):
    model = gv.GraphModel()
    scene = gv.GraphScene()

    partition_graph = TLEX.Partitioner.partition_graph(graph)

    line = 0
    for partition in partition_graph["main_graphs"]:
        count = 0
        for node in partition.nodes.values():
            xpos = (count % max_columns) * horizontal_distance
            ypos = line + (count // max_columns) * vertical_distance
            model.addNode(node.get_id_str())
            if isinstance(node, Instance.Instance):
                text = graph.events[node.event].stem
            elif isinstance(node, TimeX.TimeX):
                text = node.value
            else:
                text = ""
            scene.addItem(gv.NodeItem(node.get_id_str(), xpos, ypos, text=text))
            count += 1
        line += vertical_distance

    for partition in partition_graph["subordination_graphs"]:
        count = 0
        for node in partition.nodes.values():
            xpos = (count % max_columns) * horizontal_distance
            ypos = line + (count // max_columns) * vertical_distance
            model.addNode(node.get_id_str())
            if isinstance(node, Instance.Instance):
                text = graph.events[node.event].stem
            elif isinstance(node, TimeX.TimeX):
                text = node.value
            else:
                text = ""
            scene.addItem(gv.NodeItem(node.get_id_str(), xpos, ypos, text=text))
            count += 1
        line += vertical_distance

    # cont = 0
    # for node in graph.nodes.values():
    #     xpos = (cont % 10) * 100
    #     ypos = (cont // 10) * 100
    #     model.addNode(node.get_id_str())
    #     scene.addItem(ge.NodeItem(node.get_id_str(), xpos, ypos))
    #     cont += 1

    linklist = list(graph.links.values()) + list(tlex.s_links)
    linklist.sort(key=lambda x: (x.start_node, x.related_to_node))
    linklistlist = [[linklist[0]]]
    for link in linklist[1:]:
        if link.start_node == linklistlist[-1][-1].start_node and link.related_to_node == linklistlist[-1][-1].related_to_node:
            linklistlist[-1].append(link)
        else:
            linklistlist.append([link])

    for llist in linklistlist:
        nlinks = len(llist) // 2 #+ 1
        for link in llist:
            model.addEdge(link.start_node, link.related_to_node)
            start_node = scene.getNodeItem(link.start_node)
            end_node = scene.getNodeItem(link.related_to_node)
            if not start_node is None and not end_node is None:
                color = Qt.black if link.link_tag == "TLINK" else Qt.red if link.link_tag == "SLINK" else Qt.blue
                edgeitem = gv.EdgeItem(start_node, end_node, text=link.rel_type, text_color = QColor(color).darker(150), link_color = color, curvature=0.2*nlinks)
                scene.addItem(edgeitem)
                nlinks -= 1
    return scene

def draw(graph, tlex):
    app = QApplication(sys.argv)
    scene = getScene(graph, tlex)
    window = mw.MainWindow(scene)
    window.show()
    sys.exit(app.exec())

def visualize(filepath):
    graph = Graph.Graph(filepath = filepath)
    tlex = TLEX.TLEX(graph=graph)

    draw(graph, tlex)

    # print("Partitions:\n")
    # print(tlex.partitions)

    # print("Format = {}".format(graph))

    # print("Parsed nodes:\n")
    # for node in graph.nodes.values():
    #     print("{}, ".format(node.get_id_str()), end="")
    # print("\b\b\n\n")

    # print("Parsed links:\n")
    # for link in graph.links.values():
    #     print("{} -> {}({}) -> {}".format(link.start_node, link.rel_type, link.link_tag, link.related_to_node))

    # print("Main partition nodes:\n")
    # partition_graph = TLEX.Partitioner.partition_graph(graph)
    # for node in partition_graph["main_graphs"][0].nodes.values():
    #     print(node.get_id_str(), end=", ")
    # print("\b\b\n\n")

    # print("Subordinate partition nodes:\n")
    # count = 1
    # for partition in partition_graph["subordination_graphs"]:
    #     print("partition {}: ".format(count), end="")
    #     count += 1
    #     for node in partition.nodes.values():
    #         print(node.get_id_str(), end=", ")
    #     print("\b\b\n\n")

    # print("Indeterminacy score: {}%".format(round(tlex.indeterminacy_score*100, 2)))
    # print("Indeterminant Sections: {}".format(sorted(tlex.indeterminant_sections)))
    # print("Indeterminant Time points: ", end="")
    # for tp in sorted(tlex.indeterminant_time_points):
    #     print(tp, end=", ")
    # print("\b\b")

    # print("Main Timeline: \n\t{}\n\n".format(tlex.timeline))

    # inconsistent = tlex.get_inconsistent_partitions()
    # for g in inconsistent:
    #     for node in g.nodes.values():
    #         print("Inconsistent node: {}".format(node.get_id_str()))

    # count = 0
    # for timeline in graph.subordinate_timelines():
    #     print("Subordinate Timeline {}:\n\t{}".format(count, timeline))
    #     count += 1
