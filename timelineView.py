import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Instance, TimeX
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem
)
from PySide6.QtGui import QPen, QPainter, QColor
from PySide6.QtCore import Qt, QRectF


class TimelineView(QGraphicsView):
    def __init__(self, model):
        self.scene = TimelineScene(model)
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


class TimelineScene(QGraphicsScene):
    _minx = 0
    _miny = 0
    _maxx = 1000

    _padding = 60
    _first_lane = 60
    _lane_gap = 30
    _section_gap = 30   # extra gap between main and subordinate sections

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

    def _nodeText(self, node):
        if isinstance(node, Instance.Instance):
            return si.decodeText(self._graph.events[node.event].stem)
        if isinstance(node, TimeX.TimeX):
            return si.decodeText(node.value)
        return ""

    def _addLane(self, partition, kind, max_width, y):
        lane = TimeAxis(kind, max_width)
        lane.setPos(self._minx + self._padding, y)
        self.addItem(lane)
        for node in partition.nodes.values():
            graphNode = si.NodeItem(node.get_id_str(), text=self._nodeText(node))
            lane.addElement(graphNode)
        return y + lane.height() + self._lane_gap

    def createScene(self):
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)
        max_width = self._maxx - self._minx - 2 * self._padding

        y = self._first_lane
        for partition in partition_graph["main_graphs"]:
            y = self._addLane(partition, "main", max_width, y)
        if partition_graph["subordination_graphs"]:
            y += self._section_gap
        for partition in partition_graph["subordination_graphs"]:
            y = self._addLane(partition, "subordinate", max_width, y)

        self.setSceneRect(self._minx, self._miny,
                          self._maxx - self._minx, max(y, 200))


class TimeAxis(QGraphicsItem):
    _node_spacing = 12      # horizontal gap between adjacent nodes
    _row_height = 50        # vertical distance between sub-rows
    _node_y_offset = -20    # node center sits this far above its row's axis line

    _MAIN_COLOR = QColor(0, 0, 0)
    _SUB_COLOR = QColor(120, 120, 120)

    def __init__(self, kind, max_width):
        super().__init__()
        self._max_width = max_width
        self._kind = kind   # "main" or "subordinate"
        self._rows = [[]]   # each row: list of (center_x, width)
        self._cursor_x = 0
        color = self._MAIN_COLOR if kind == "main" else self._SUB_COLOR
        self._pen = QPen(color, 2 if kind == "main" else 1)
        if kind != "main":
            self._pen.setStyle(Qt.DashLine)
        self.setZValue(-1)

    def addElement(self, element):
        rect = element.rect() if hasattr(element, 'rect') else element.boundingRect()
        w = rect.width()
        if self._cursor_x > 0 and self._cursor_x + w > self._max_width:
            self._rows.append([])
            self._cursor_x = 0
        cx = self._cursor_x + w / 2
        cy = (len(self._rows) - 1) * self._row_height + self._node_y_offset
        element.setParentItem(self)
        element.setPos(cx, cy)
        self._rows[-1].append((cx, w))
        self._cursor_x += w + self._node_spacing

    def height(self):
        return len(self._rows) * self._row_height

    def boundingRect(self):
        top = self._node_y_offset - 4
        h = (len(self._rows) - 1) * self._row_height - top + 4
        return QRectF(0, top, self._max_width, h)

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        for i, row in enumerate(self._rows):
            y = i * self._row_height
            end_x = (row[-1][0] + row[-1][1] / 2) if row else self._max_width
            painter.drawLine(0, y, end_x, y)
