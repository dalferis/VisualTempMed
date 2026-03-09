from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QStackedWidget,
    QLabel, QCheckBox, QSlider, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt
import graphView as gv
import timelineView as tv

class MainWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()

        self.setWindowTitle("Visualizador de líneas temporales en contexto médico")
        self.resize(1200, 800)

        self.graphView = gv.GraphView(model)
        self.graphScene = self.graphView.scene
        self.timelineView = tv.TimelineView(model)
        self.timelineScene = self.timelineView.scene

        self.stack = QStackedWidget()
        self.stack.addWidget(self.graphView)
        self.stack.addWidget(self.timelineView)

        self.setCentralWidget(self.stack)
        self.stack.setCurrentWidget(self.graphView)

        self.create_control_panel()

    def create_control_panel(self):
        dock = QDockWidget("Control panel", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Controls

        # Radio button
        self.display_graph = QRadioButton("Graph")
        self.display_timeline = QRadioButton("Timeline")
        self.display_graph.setChecked(True)
        self.display_radio_group = QButtonGroup()
        self.display_radio_group.addButton(self.display_graph)
        self.display_radio_group.addButton(self.display_timeline)
        self.display_graph.toggled.connect(self.change_view)
        layout.addWidget(self.display_graph)
        layout.addWidget(self.display_timeline)

        # Show IDs checkbox
        self.chkbxShowId = QCheckBox("Show IDs")
        self.chkbxShowId.setChecked(True)
        self.chkbxShowId.stateChanged.connect(self.toggle_show_ids)
        layout.addWidget(self.chkbxShowId)

        # Edge thickness slider
        layout.addWidget(QLabel("Edge thickness"))
        self.sliderEdgeThickness = QSlider(Qt.Horizontal)
        self.sliderEdgeThickness.setMinimum(1)
        self.sliderEdgeThickness.setMaximum(10)
        self.sliderEdgeThickness.setValue(2)
        layout.addWidget(self.sliderEdgeThickness)
        self.sliderEdgeThickness.valueChanged.connect(self.update_edge_width)

        # Properties
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def change_view(self, activo):
        if activo:
            self.stack.setCurrentWidget(self.graphView)
        else:
            self.stack.setCurrentWidget(self.timelineView)

    def update_edge_width(self, value):
        for item in self.graphScene.items():
            if isinstance(item, gv.EdgeItem):
                pen = item.pen()
                pen.setWidth(value)
                item.setPen(pen)

    def toggle_show_ids(self, state):
        for item in self.graphScene.items():
            if isinstance(item, gv.NodeItem):
                item.id_bg.setVisible(state)
                item.id_text.setVisible(state)
