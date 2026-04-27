import networkx as nx
import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import Qt


class GraphView(QGraphicsView):
    def __init__(self, model):
        self.scene = GraphScene(model)
        super().__init__(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

class GraphScene(QGraphicsScene):
    _graph: Graph.Graph
    _tlex: TLEX.TLEX

    # _window_width = 1024
    # _window_height = 1024
    _max_columns = 15
    _horizontal_distance = 150
    _vertical_distance = 80

    def __init__(self, dataModel):
        super().__init__()
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self.createScene()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, si.NodeItem):
            self.nodes[item.node_id] = item

    def isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def isCreationTimeLink(self, link):
        return self.isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self.isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def createScene(self):
        graphModel = nx.MultiDiGraph()
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)

        line = 0
        for partition in partition_graph["main_graphs"]:
            count = 0
            for node in [v for v in partition.nodes.values() if not self.isCreationTimeTimex3(v)]:
                xpos = (count % self._max_columns) * self._horizontal_distance
                ypos = line + (count // self._max_columns) * self._vertical_distance
                graphModel.add_node(node.get_id_str())
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.phrase)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                self.addItem(graphNode)
                graphNode.setPos(xpos, ypos)
                count += 1
            line += self._vertical_distance

        for partition in partition_graph["subordination_graphs"]:
            count = 0
            for node in [v for v in partition.nodes.values() if not self.isCreationTimeTimex3(v)]:
                xpos = (count % self._max_columns) * self._horizontal_distance
                ypos = line + (count // self._max_columns) * self._vertical_distance
                graphModel.add_node(node.get_id_str())
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.value)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                self.addItem(graphNode)
                graphNode.setPos(xpos, ypos)
                count += 1
            line += self._vertical_distance

        linklist = [v for v in self._graph.links.values() if not self.isCreationTimeLink(v)] + [v for v in self._tlex.s_links if not self.isCreationTimeLink(v)]
        linklist.sort(key=lambda x: (x.start_node, x.related_to_node))
        linklistlist = [[linklist[0]]]
        for link in linklist[1:]:
            if link.start_node == linklistlist[-1][-1].start_node and link.related_to_node == linklistlist[-1][-1].related_to_node:
                linklistlist[-1].append(link)
            else:
                linklistlist.append([link])

        for llist in linklistlist:
            nlinks = len(llist) // 2
            for link in llist:
                graphModel.add_edge(link.start_node, link.related_to_node)
                start_node = self.nodes.get(link.start_node, None)
                end_node = self.nodes.get(link.related_to_node, None)
                if not start_node is None and not end_node is None:
                    color = Qt.black if link.link_tag == "TLINK" else Qt.red if link.link_tag == "SLINK" else Qt.blue
                    edgeitem = si.EdgeItem(start_node, end_node, text=link.rel_type, text_color = QColor(color).darker(150), link_color = color, curvature=0.2*nlinks)
                    self.addItem(edgeitem)
                    nlinks -= 1
