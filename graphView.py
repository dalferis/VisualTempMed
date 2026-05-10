import networkx as nx
import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtCore import Qt, Signal


class GraphView(QGraphicsView):
    def __init__(self, model):
        self.scene = GraphScene(model)
        super().__init__(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(factor, factor)
            else:
                self.scale(1 / factor, 1 / factor)
        else:
            super().wheelEvent(event)

class GraphScene(QGraphicsScene):
    nodeClicked = Signal(str)

    _graph: Graph.Graph
    _tlex: TLEX.TLEX

    _max_columns = 15
    _horizontal_distance = 150
    _vertical_distance = 80
    _partition_gap = 40  # extra vertical space between successive partitions
    _partition_label_margin = 12  # horizontal gap between partition header and first node

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

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        for it in self.items(event.scenePos()):
            owner = it
            while owner is not None and not isinstance(owner, si.NodeItem):
                owner = owner.parentItem()
            if isinstance(owner, si.NodeItem):
                self.nodeClicked.emit(owner.node_id)
                return

    def isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def isCreationTimeLink(self, link):
        return self.isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self.isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def _headerFont(self):
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font

    def _drawPartitions(self, partitions, kind, line, use_phrase, graphModel, header_x):
        displayed_idx = 0
        for partition in partitions:
            displayed_idx += 1

            first_node = None
            x_shift = 0  # horizontal offset so the first node's left edge sits at x=0
            count = 0
            for node in partition:
                graphModel.add_node(node.get_id_str())
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.phrase if use_phrase else node.value)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                self.addItem(graphNode)
                if first_node is None:
                    first_node = graphNode
                    x_shift = graphNode.rect().width() / 2
                xpos = x_shift + (count % self._max_columns) * self._horizontal_distance
                ypos = line + (count // self._max_columns) * self._vertical_distance
                graphNode.setPos(xpos, ypos)
                count += 1

            # Header left-aligned at a fixed x for the whole scene, vertically
            # centered on the first row of nodes.
            header = QGraphicsTextItem(f"{kind} #{displayed_idx}")
            header.setFont(self._headerFont())
            header.setDefaultTextColor(Qt.darkGray)
            header.setAcceptedMouseButtons(Qt.NoButton)
            self.addItem(header)
            header_rect = header.boundingRect()
            first_node_rect = first_node.rect().translated(first_node.pos())
            header.setPos(
                header_x,
                first_node_rect.center().y() - header_rect.height() / 2,
            )

            rows = (count - 1) // self._max_columns + 1
            line += rows * self._vertical_distance + self._partition_gap
        return line

    def createScene(self):
        graphModel = nx.MultiDiGraph()
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)

        def visible(partition):
            return [v for v in partition.nodes.values() if not self.isCreationTimeTimex3(v)]

        main_partitions = [v for v in (visible(p) for p in partition_graph["main_graphs"]) if v]
        sub_partitions = [v for v in (visible(p) for p in partition_graph["subordination_graphs"]) if v]

        fm = QFontMetrics(self._headerFont())
        max_header_width = 0
        if main_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Main #{len(main_partitions)}"))
        if sub_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Subordinate #{len(sub_partitions)}"))
        header_x = -max_header_width - self._partition_label_margin

        line = 0
        line = self._drawPartitions(main_partitions, "Main", line, use_phrase=True, graphModel=graphModel, header_x=header_x)
        line = self._drawPartitions(sub_partitions, "Subordinate", line, use_phrase=False, graphModel=graphModel, header_x=header_x)

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
