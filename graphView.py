import math
import networkx as nx
from pytlex_core.algorithms import TLEX
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsPathItem, QGraphicsTextItem
)
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF, QLineF
from PySide6.QtWidgets import QGraphicsItem
from pytlex_core.data import Graph, Instance, TimeX

class GraphView(QGraphicsView):
    def __init__(self, model):
        self.scene = GraphScene(model)
        super().__init__(self.scene)
        self.setRenderHint(self.renderHints())
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

class GraphModel:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def addNode(self, node_id):
        self.graph.add_node(node_id)

    def addEdge(self, u, v):
        return self.graph.add_edge(u, v)

class GraphScene(QGraphicsScene):
    _graph: Graph.Graph
    _tlex: TLEX.TLEX

    _window_width = 1024
    _window_height = 1024
    _max_columns = 15
    _horizontal_distance = 150
    _vertical_distance = 80

    def __init__(self, dataModel):
        super().__init__()
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self.scene()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, NodeItem):
            self.nodes[item.node_id] = item

    def getNodeItem(self, node_id):
        return self.nodes.get(node_id, None)

    def scene(self):
        graphModel = GraphModel()
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)

        line = 0
        for partition in partition_graph["main_graphs"]:
            count = 0
            for node in partition.nodes.values():
                xpos = (count % self._max_columns) * self._horizontal_distance
                ypos = line + (count // self._max_columns) * self._vertical_distance
                graphModel.addNode(node.get_id_str())
                if isinstance(node, Instance.Instance):
                    text = self._graph.events[node.event].stem
                elif isinstance(node, TimeX.TimeX):
                    text = node.value
                else:
                    text = ""
                self.addItem(NodeItem(node.get_id_str(), xpos, ypos, text=text))
                count += 1
            line += self._vertical_distance

        for partition in partition_graph["subordination_graphs"]:
            count = 0
            for node in partition.nodes.values():
                xpos = (count % self._max_columns) * self._horizontal_distance
                ypos = line + (count // self._max_columns) * self._vertical_distance
                graphModel.addNode(node.get_id_str())
                if isinstance(node, Instance.Instance):
                    text = self._graph.events[node.event].stem
                elif isinstance(node, TimeX.TimeX):
                    text = node.value
                else:
                    text = ""
                self.addItem(NodeItem(node.get_id_str(), xpos, ypos, text=text))
                count += 1
            line += self._vertical_distance

        linklist = list(self._graph.links.values()) + list(self._tlex.s_links)
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
                graphModel.addEdge(link.start_node, link.related_to_node)
                start_node = self.getNodeItem(link.start_node)
                end_node = self.getNodeItem(link.related_to_node)
                if not start_node is None and not end_node is None:
                    color = Qt.black if link.link_tag == "TLINK" else Qt.red if link.link_tag == "SLINK" else Qt.blue
                    edgeitem = EdgeItem(start_node, end_node, text=link.rel_type, text_color = QColor(color).darker(150), link_color = color, curvature=0.2*nlinks)
                    self.addItem(edgeitem)
                    nlinks -= 1


class NodeItem(QGraphicsRectItem):
    def __init__(self, node_id, x, y, text=""):
        self.node_id = node_id
        self.edges = []

        self.label = QGraphicsTextItem(text)
        self.label.setDefaultTextColor(Qt.blue)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label.setFont(font)

        text_rect = self.label.boundingRect()
        padding = -2
        width = text_rect.width() + padding
        height = text_rect.height() + padding

        super().__init__(-width/2, -height/2, width, height)
        self.setPos(x, y)

        self.setBrush(QBrush(Qt.lightGray))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.label.setParentItem(self)
        self.label.setPos(-text_rect.width()/2, -text_rect.height()/2)

        self.create_id_badge()

    def create_id_badge(self):
        padding = -2

        self.id_text = QGraphicsTextItem(str(self.node_id), self)
        self.id_text.setDefaultTextColor(Qt.white)

        font = QFont()
        font.setPointSize(6)
        font.setBold(True)
        self.id_text.setFont(font)

        text_rect = self.id_text.boundingRect()

        badge_width = text_rect.width() + padding * 2
        badge_height = text_rect.height() + padding * 2

        self.id_bg = QGraphicsRectItem(self)
        self.id_bg.setBrush(QBrush(Qt.darkGray))
        self.id_bg.setPen(QPen(Qt.black, 1))

        node_rect = self.rect()

        x = node_rect.left() - 4
        y = node_rect.top() - 10

        self.id_bg.setRect(x, y, badge_width, badge_height)

        self.id_text.setPos(x + padding, y + padding)

        self.id_bg.setZValue(2)
        self.id_text.setZValue(3)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

class EdgeItem(QGraphicsPathItem):
    def __init__(self, source, target, text="", text_color=Qt.black, link_color=Qt.black, curvature=0.0):
        super().__init__()

        self.source = source
        self.target = target
        self.curvature = curvature

        self.setPen(QPen(link_color, 2))
        self.setZValue(-1)

        source.add_edge(self)
        target.add_edge(self)

        self.label = QGraphicsTextItem(text, self)
        self.label.setDefaultTextColor(text_color)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.update_position()
        return super().itemChange(change, value)

    def intersect_line_with_rect(self, center_from, center_to, rect, item_pos):
        line = QLineF(center_from, center_to)
        r = rect.translated(item_pos)

        edges = [
            QLineF(r.topLeft(), r.topRight()),
            QLineF(r.topRight(), r.bottomRight()),
            QLineF(r.bottomRight(), r.bottomLeft()),
            QLineF(r.bottomLeft(), r.topLeft())
        ]

        for edge in edges:
            intersection_type, point = line.intersects(edge)
            if intersection_type == QLineF.BoundedIntersection:
                return point

        return center_from

    def has_obstacle_between(self, start, end):
        scene = self.scene()
        if not scene:
            return False

        line = QLineF(start, end)

        for item in scene.items():

            if not isinstance(item, NodeItem):
                continue

            if item is self.source or item is self.target:
                continue

            rect = item.rect().translated(item.pos())

            edges = [
                QLineF(rect.topLeft(), rect.topRight()),
                QLineF(rect.topRight(), rect.bottomRight()),
                QLineF(rect.bottomRight(), rect.bottomLeft()),
                QLineF(rect.bottomLeft(), rect.topLeft())
            ]

            for edge in edges:
                intersection_type, _ = line.intersects(edge)
                if intersection_type == QLineF.BoundedIntersection:
                    return True

        return False

    def update_position(self):
        rect1 = self.source.rect()
        rect2 = self.target.rect()

        center1 = self.source.pos() + rect1.center()
        center2 = self.target.pos() + rect2.center()

        start = self.intersect_line_with_rect(
            center1, center2, rect1, self.source.pos()
        )

        end = self.intersect_line_with_rect(
            center2, center1, rect2, self.target.pos()
        )

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        base_angle = math.atan2(dy, dx)

        path = QPainterPath()
        path.moveTo(start)

        ctrl = None
        if self.curvature != 0:
            curvature = self.curvature
        elif self.has_obstacle_between(start, end):
            curvature = 0.25
        else:
            curvature = 0.0

        if curvature != 0:
            ctrl = QPointF(
                (start.x() + end.x()) / 2 - dy * curvature,
                (start.y() + end.y()) / 2 + dx * curvature
            )
            path.quadTo(ctrl, end)
            tx = end.x() - ctrl.x()
            ty = end.y() - ctrl.y()
            angle = math.atan2(ty, tx)
        else:
            path.lineTo(end)
            angle = base_angle

        # Arrow
        arrow_size = 12
        arrow_p1 = end - QPointF(
            arrow_size * math.cos(angle - math.pi / 6),
            arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = end - QPointF(
            arrow_size * math.cos(angle + math.pi / 6),
            arrow_size * math.sin(angle + math.pi / 6)
        )

        path.moveTo(end)
        path.lineTo(arrow_p1)
        path.moveTo(end)
        path.lineTo(arrow_p2)
        self.setPath(path)

        # Label
        if curvature != 0 and ctrl is not None:
            t = 0.5

            # Real point on the curve (quadratic Bézier)
            x = (1 - t)**2 * start.x() + 2 * (1 - t) * t * ctrl.x() + t**2 * end.x()
            y = (1 - t)**2 * start.y() + 2 * (1 - t) * t * ctrl.y() + t**2 * end.y()

            label_pos = QPointF(x, y)

            # Real tangent of the curve
            tx = 2*(1 - t)*(ctrl.x() - start.x()) + 2*t*(end.x() - ctrl.x())
            ty = 2*(1 - t)*(ctrl.y() - start.y()) + 2*t*(end.y() - ctrl.y())

            length = math.hypot(tx, ty)

            if length != 0:
                nx = -ty / length
                ny = tx / length

                offset = 15
                label_pos += QPointF(nx * offset, ny * offset)

        else:
            # Beeline
            label_pos = QPointF(
                (start.x() + end.x()) / 2,
                (start.y() + end.y()) / 2
            )

        # Center text
        rect = self.label.boundingRect()
        label_pos -= QPointF(rect.width() / 2, rect.height() / 2)

        self.label.setPos(label_pos)
