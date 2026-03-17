import graphView as gv
import timelineView as tv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QCheckBox, QSlider, QRadioButton, QButtonGroup, QGridLayout
)

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
        self.stack.setCurrentWidget(self.timelineView)
        self.create_control_panel()

    def create_control_panel(self):
        dock = QDockWidget("Control panel", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Layout with common controls:
        layoutCommon = QGridLayout()
        layout.addLayout(layoutCommon)
        # - Radio buttons for view selection
        self.radioGraph = QRadioButton("Graph")
        self.radioTimeline = QRadioButton("Timeline")
        self.radioTimeline.setChecked(True)
        self.radiogroupView = QButtonGroup(self)
        self.radiogroupView.addButton(self.radioGraph)
        self.radiogroupView.addButton(self.radioTimeline)
        self.radiogroupView.setId(self.radioGraph, 0)
        self.radiogroupView.setId(self.radioTimeline, 1)
        self.radiogroupView.idClicked.connect(self.change_view)
        layoutCommon.addWidget(self.radioGraph, 0, 0)
        layoutCommon.addWidget(self.radioTimeline, 0, 1)
        # - Checkbox for showing IDs
        self.chkbxShowId = QCheckBox("Show IDs")
        self.chkbxShowId.setChecked(True)
        self.chkbxShowId.stateChanged.connect(self.toggle_show_ids)
        layoutCommon.addWidget(self.chkbxShowId, 1, 0)

        # Layout with controls:
        self.stackControl = QStackedWidget()
        self.stackControl.addWidget(self.create_graph_controls())
        self.stackControl.addWidget(self.create_timeline_controls())
        layout.addWidget(self.stackControl)

        # Properties
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def create_graph_controls(self):
        widget = QWidget()
        # Layout with graph controls:
        layout = QVBoxLayout(widget)
        # - Slider for edge thickness
        layout.addWidget(QLabel("Edge thickness"))
        self.sliderEdgeThickness = QSlider(Qt.Horizontal)
        self.sliderEdgeThickness.setMinimum(1)
        self.sliderEdgeThickness.setMaximum(10)
        self.sliderEdgeThickness.setValue(2)
        layout.addWidget(self.sliderEdgeThickness)
        self.sliderEdgeThickness.valueChanged.connect(self.update_edge_width)
        return widget

    def create_timeline_controls(self):
        ####### TODO: Este control solo es un ejemplo
        widget = QWidget()
        # Layout with timeline controls:
        layout = QVBoxLayout(widget)
        # - Checkbox for showing IDs
        self.chkbxShowIdTimeline = QCheckBox("Show ID lanes")
        self.chkbxShowIdTimeline.setChecked(True)
        self.chkbxShowIdTimeline.stateChanged.connect(self.toggle_show_ids)
        layout.addWidget(self.chkbxShowIdTimeline)
        return widget

    def change_view(self, index):
        self.stack.setCurrentIndex(index)
        self.stackControl.setCurrentIndex(index)

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
