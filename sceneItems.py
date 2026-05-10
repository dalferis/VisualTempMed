import html
import math
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath, QPainterPathStroker, QFont
from PySide6.QtCore import Qt, QPointF, QLineF


def decodeText(s):
    if not s:
        return s
    return html.unescape(s)


class NodeItem(QGraphicsRectItem):
    EVENT_BRUSH = QBrush(Qt.lightGray)
    TIMEX_BRUSH = QBrush(QColor(200, 230, 201))  # soft green

    def __init__(self, node_id, text=""):
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

        is_timex = isinstance(node_id, str) and len(node_id) > 1 and node_id[0] == 't' and node_id[1:].isdigit()
        self.setBrush(self.TIMEX_BRUSH if is_timex else self.EVENT_BRUSH)
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.label.setParentItem(self)
        self.label.setPos(-text_rect.width()/2, -text_rect.height()/2)

        self.createIdBadge()

    def createIdBadge(self):
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

    def addEdge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.updatePosition()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsPathItem):
    _hit_width = 8

    def __init__(self, source, target, text="", text_color=Qt.black, link_color=Qt.black, curvature=0.0):
        super().__init__()

        self.source = source
        self.target = target
        self.curvature = curvature

        self.setPen(QPen(link_color, 2))
        self.setZValue(-1)

        source.addEdge(self)
        target.addEdge(self)

        self.label = QGraphicsTextItem(text, self)
        self.label.setDefaultTextColor(text_color)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(self._hit_width)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.updatePosition()
        return super().itemChange(change, value)

    def intersectLineWithRect(self, center_from, center_to, rect, item_pos):
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

    def hasObstacleBetween(self, start, end):
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

    def updatePosition(self):
        rect1 = self.source.rect()
        rect2 = self.target.rect()

        center1 = self.source.pos() + rect1.center()
        center2 = self.target.pos() + rect2.center()

        start = self.intersectLineWithRect(
            center1, center2, rect1, self.source.pos()
        )

        end = self.intersectLineWithRect(
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
        elif self.hasObstacleBetween(start, end):
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
            # Beeline - offset the label perpendicular to the segment so it
            # doesn't overlap the edge line itself.
            label_pos = QPointF(
                (start.x() + end.x()) / 2,
                (start.y() + end.y()) / 2
            )
            length = math.hypot(dx, dy)
            if length != 0:
                nx = -dy / length
                ny = dx / length
                # Prefer placing the label above the edge in screen coords.
                if ny > 0:
                    nx, ny = -nx, -ny
                offset = 15
                label_pos += QPointF(nx * offset, ny * offset)

        # Center text
        rect = self.label.boundingRect()
        label_pos -= QPointF(rect.width() / 2, rect.height() / 2)

        self.label.setPos(label_pos)
