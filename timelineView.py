from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtGui import QPen, QBrush, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF, QLineF

class TimelineView(QGraphicsView):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.build_timeline()

    def build_timeline(self):

        y = 0
        print("buildig timeline")
        # for node in self.model.graph.nodes:

        #     rect = QGraphicsRectItem(0, y, 200, 40)
        #     text = QGraphicsTextItem(node)
        #     text.setPos(10, y + 10)

        #     self.scene.addItem(rect)
        #     self.scene.addItem(text)

        #     y += 60