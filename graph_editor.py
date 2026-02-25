from re import I
import sys
import math
import networkx as nx
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem, QToolTip
)
from PySide6.QtGui import QPen, QBrush, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsItem


class GraphModel:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def addNode(self, node_id):
        self.graph.add_node(node_id)

    def addEdge(self, u, v):
        return self.graph.add_edge(u, v)


class GraphScene(QGraphicsScene):
    # def __init__(self):
    #     super().__init__()
    #     self.nodes = {}
    #     self.edges = []

    # def addItem(self, item):
    #     if isinstance(item, NodeItem):
    #         super().addItem(item)
    #         self.nodes[item.node_id] = item
    #     elif isinstance(item, EdgeItem):
    #         edge = {}
    #         edge['source'] = item.source.node_id
    #         edge['target'] = item.target.node_id
    #         a = [e for e in self.edges if e.source.node_id == item.source.node_id]
    #         edge['curvature']
    #         self.edges.append(item)

    def __init__(self):
        super().__init__()
        self.nodes = {}

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, NodeItem):
            self.nodes[item.node_id] = item

    def getNodeItem(self, node_id):
        return self.nodes.get(node_id, None)


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, radius=25, text=None):
        super().__init__(-radius, -radius, radius*2, radius*2)

        self.node_id = node_id
        self.radius = radius
        self.edges = []
        self.setPos(x, y)

        self.setBrush(QBrush(Qt.lightGray))
        self.setPen(QPen(Qt.black, 2))

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.label = QGraphicsTextItem(node_id, self)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.center_label()

        if text:
            self.label2 = QGraphicsTextItem(text, self)
            self.label2.setDefaultTextColor(Qt.blue)

            rect = self.label2.boundingRect()

            self.label2.setPos(
                -rect.width() / 2,
                -radius - rect.height() - 3
            )

            self.label2.setZValue(1)

    def center_label(self):
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width()/2, -rect.height()/2)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.text)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()


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

        self.label = QGraphicsTextItem(text)
        self.label.setDefaultTextColor(text_color)

        self.update_position()

    def update_position(self):
        p1 = self.source.pos()
        p2 = self.target.pos()

        # Dirección
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        base_angle = math.atan2(dy, dx)

        # Punto en borde del nodo origen
        start = QPointF(
            p1.x() + self.source.radius * math.cos(base_angle),
            p1.y() + self.source.radius * math.sin(base_angle)
        )

        # Punto en borde del nodo destino
        end = QPointF(
            p2.x() - self.target.radius * math.cos(base_angle),
            p2.y() - self.target.radius * math.sin(base_angle)
        )

        path = QPainterPath()
        path.moveTo(start)

        ctrl = None
        if self.curvature != 0:
            ctrl = QPointF(
                (start.x() + end.x()) / 2 - dy * self.curvature,
                (start.y() + end.y()) / 2 + dx * self.curvature
            )
            path.quadTo(ctrl, end)
            tx = end.x() - ctrl.x()
            ty = end.y() - ctrl.y()
            angle = math.atan2(ty, tx)
        else:
            path.lineTo(end)
            angle = base_angle

        # Flecha
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

        # Etiqueta
        if self.curvature != 0 and ctrl is not None:
            t = 0.5

            # Punto real en la curva (Bézier)
            x = (1 - t)**2 * start.x() + 2 * (1 - t) * t * ctrl.x() + t**2 * end.x()
            y = (1 - t)**2 * start.y() + 2 * (1 - t) * t * ctrl.y() + t**2 * end.y()

            label_pos = QPointF(x, y)

            tx = 2*(1 - t)*(ctrl.x() - start.x()) + 2*t*(end.x() - ctrl.x())
            ty = 2*(1 - t)*(ctrl.y() - start.y()) + 2*t*(end.y() - ctrl.y())

            length = math.hypot(tx, ty)

            if length != 0:
                # Vector normal
                nx = -ty / length
                ny = tx / length

                offset = 15
                label_pos += QPointF(nx * offset, ny * offset)
        else:
            # Línea recta
            label_pos = QPointF(
                (start.x() + end.x()) / 2,
                (start.y() + end.y()) / 2
            )

        # Centrar el texto respecto al punto calculado
        rect = self.label.boundingRect()
        label_pos -= QPointF(rect.width() / 2, rect.height() / 2)

        self.label.setPos(label_pos)


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(self.renderHints())
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)


# def main():
#     app = QApplication(sys.argv)

#     model = GraphModel()
#     scene = QGraphicsScene()

#     view = GraphView(scene)
#     view.setWindowTitle("Visual Temporal Medical")
#     view.resize(800, 600)

#     model.add_node("A")
#     model.add_node("B")

#     nodeA = NodeItem("A", -100, 0)
#     nodeB = NodeItem("B", 100, 0)

#     scene.addItem(nodeA)
#     scene.addItem(nodeB)

#     model.add_edge("A", "B")
#     model.add_edge("A", "B")
#     model.add_edge("A", "B")

#     e1 = EdgeItem(nodeA, nodeB, curvature=0.0)
#     e2 = EdgeItem(nodeA, nodeB, curvature=0.2)
#     e3 = EdgeItem(nodeA, nodeB, curvature=-0.2)

#     scene.addItem(e1)
#     scene.addItem(e2)
#     scene.addItem(e3)

#     view.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
