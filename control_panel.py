import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout,
    QLabel, QPushButton, QCheckBox, QSlider
)
from PySide6.QtCore import Qt
import graph_editor as ge


class MainWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()

        self.setWindowTitle("Visualizador de líneas temporales en contexto médico")
        self.resize(1200, 800)

        self.scene = scene
        self.view = ge.GraphView(self.scene)
        self.setCentralWidget(self.view)

        self.create_control_panel()

    def create_control_panel(self):
        dock = QDockWidget("Control panel", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Controles de ejemplo
        self.curvature_checkbox = QCheckBox("Activate automatic curvature")
        self.curvature_checkbox.setChecked(True)
        layout.addWidget(self.curvature_checkbox)

        self.arrow_checkbox = QCheckBox("Show arrows")
        self.arrow_checkbox.setChecked(True)
        layout.addWidget(self.arrow_checkbox)

        layout.addWidget(QLabel("Edge thickness"))

        self.edge_width_slider = QSlider(Qt.Horizontal)
        self.edge_width_slider.setMinimum(1)
        self.edge_width_slider.setMaximum(10)
        self.edge_width_slider.setValue(2)
        layout.addWidget(self.edge_width_slider)

        layout.addStretch()

        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Conectar señales
        self.edge_width_slider.valueChanged.connect(self.update_edge_width)

    def update_edge_width(self, value):
        for item in self.scene.items():
            if isinstance(item, ge.EdgeItem):
                pen = item.pen()
                pen.setWidth(value)
                item.setPen(pen)
