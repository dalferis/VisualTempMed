import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from xmlrpc.client import DateTime
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtGui import QPen, QBrush, QPainterPath, QFont, QPainter
from PySide6.QtCore import Qt, QPointF, QLineF, QRectF

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
    _maxy = 800

    _first_lane = 80
    _lane_height = 80
    _time_resolution = 50

    def __init__(self, dataModel):
        super().__init__()
        self.setSceneRect(self._minx, self._miny, self._maxx - self._minx, self._maxy - self._miny)
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self.createScene()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, si.NodeItem):
            self.nodes[item.node_id] = item

    def createScene(self):
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)
        maxTime = 0
        for partition in partition_graph["main_graphs"]:
            maxTime = max(maxTime, len(partition.nodes))

        subLanes = []
        laneCount = 0
        for partition in partition_graph["main_graphs"]:
            lane = TimeAxis("Main #"+str(laneCount), laneCount, self._minx, self._miny, self._maxx, self._maxy)
            subLanes.append(lane)
            lane.setScale(maxTime-1)
            self.addItem(lane)
            count = 0
            for node in partition.nodes.values():
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.value)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                lane.addElement(count, graphNode)
                count += 1
            laneCount += 1

        mainCount = laneCount
        for partition in partition_graph["subordination_graphs"]:
            lane = TimeAxis("Subordinate #"+str(laneCount-mainCount), laneCount, self._minx, self._miny, self._maxx, self._maxy)
            subLanes.append(lane)
            lane.setScale(maxTime-1)
            self.addItem(lane)
            count = 0
            for node in partition.nodes.values():
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.value)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                lane.addElement(count, graphNode)
                count += 1
            laneCount += 1

class TimeAxis(QGraphicsItem):
    # physical dimensions (pixels)
    _first_lane = 80
    _lane_height = 80
    _time_resolution = 50
    _padding = 100

    # logical dimensions (time units)
    _start_time = 0
    _tick_interval = 5
    _tick_num_intervals = 5
    _tick_height = 10
    _duration: int

    # pixels per time unit
    _time_scale: float

    def __init__(self, labelText, index, minx, miny, maxx, maxy):
        super().__init__()
        self._minx = minx
        self._miny = miny
        self._maxx = maxx
        self._maxy = maxy
        self.width = self._maxx - self._minx - 2*self._padding
        self.label = QGraphicsTextItem(labelText, self)
        self.label.setPos(0, self.label.boundingRect().height())
        self.setPos(minx + self._padding, self._first_lane + index * self._lane_height)
        self.setZValue(-1)

    def addElement(self, time, element):
        element.setParentItem(self)
        x = time * self._time_resolution
        element.setPos(x, -10)

    def boundingRect(self):
        return QRectF(0, -10, self.width, 20)

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(0, 0, self.width, 0)
        painter.setPen(QPen(Qt.black, 1))
        t = self._start_time
        while t <= self._end_time:
            x = t * self._time_resolution
            painter.drawLine(x, -self._tick_height, x, self._tick_height)
            painter.drawText(x, 20, str(int(t)))
            t += self._tick_interval

    def setScale(self, maxTime):
        self._end_time = maxTime
        self._tick_num_intervals = maxTime
        self._tick_interval = max(1, maxTime // self._tick_num_intervals)
        self._time_resolution = (self._maxx - self._minx - 2*self._padding) / maxTime
        self.update()