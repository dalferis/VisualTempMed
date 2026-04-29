from tkinter import SE
import sceneItems as si
import graphView as gv
import timelineView as tlv
import textView as txv
from dataModel import DataModel
from pytlex_core.data import Graph
from pytlex_core.algorithms import TLEX, Partitioner
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QCheckBox, QSlider, QRadioButton, QButtonGroup, QGridLayout, QSizePolicy,
    QFileDialog, QMessageBox
)

class MainWindow(QMainWindow):
    _initialPanel = "graph"
    #_initialPanel = "timeline"
    #_initialPanel = "text"


    def __init__(self, model=None):
        super().__init__()

        self.setWindowTitle("Visualizador de líneas temporales en contexto médico")
        self.resize(1200, 800)

        self.graphView = self.graphScene = None
        self.timelineView = self.timelineScene = None
        self.textView = self.textScene = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.createMenuBar()
        self.createControlPanel()
        self.createAttributesPanel()
        self.statusBar().showMessage("No file loaded")
        if model is not None:
            self.loadModel(model)

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        openAction = QAction("&Open TimeML file...", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.openTimeMlFile)
        fileMenu.addAction(openAction)
        fileMenu.addSeparator()
        exitAction = QAction("E&xit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        helpMenu = menuBar.addMenu("&Help")
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)

    def openTimeMlFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open TimeML file", "", "TimeML files (*.tml);;All files (*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            graph = Graph.Graph(time_ml_string=content)
            tlex = TLEX.TLEX(graph=graph)
            model = DataModel(graph, tlex)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{e}")
            return
        self.loadModel(model, path)

    def showAbout(self):
        QMessageBox.about(
            self,
            "About",
            "Visualizador de líneas temporales en contexto médico\n\nPFG UNED 2025-2026"
        )

    def loadModel(self, model, filepath=None):
        currentIndex = self.stack.currentIndex()
        if currentIndex < 0:
            currentIndex = self.radiogroupView.checkedId()
        for view in (self.graphView, self.timelineView, self.textView):
            if view is None:
                continue
            self.stack.removeWidget(view)
            view.deleteLater()
        self.graphView = self.graphScene = None
        self.timelineView = self.timelineScene = None
        self.textView = self.textScene = None
        # Reset pytlex_core's module-level SLink set; it leaks across files:
        Partitioner.single_links.clear()
        self.graphView = gv.GraphView(model)
        self.graphScene = self.graphView.scene
        self.timelineView = tlv.TimelineView(model)
        self.timelineScene = self.timelineView.scene
        self.textView = txv.TextView(model)
        self.textScene = self.textView.scene
        self.stack.addWidget(self.graphView)
        self.stack.addWidget(self.timelineView)
        self.stack.addWidget(self.textView)
        self.stack.setCurrentIndex(currentIndex)
        self.toggleShowIds(self.chkbxShowId.isChecked())
        self.statusBar().showMessage(filepath if filepath else "")

    def createControlPanel(self):
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
        self.radioText = QRadioButton("Text")
        self.radioTimeline.setChecked(self._initialPanel=="timeline")
        self.radioGraph.setChecked(self._initialPanel=="graph")
        self.radioText.setChecked(self._initialPanel=="text")
        self.radiogroupView = QButtonGroup(self)
        self.radiogroupView.addButton(self.radioGraph)
        self.radiogroupView.addButton(self.radioTimeline)
        self.radiogroupView.addButton(self.radioText)
        self.radiogroupView.setId(self.radioGraph, 0)
        self.radiogroupView.setId(self.radioTimeline, 1)
        self.radiogroupView.setId(self.radioText, 2)
        self.radiogroupView.idClicked.connect(self.changeView)
        layoutCommon.addWidget(self.radioGraph, 0, 0)
        layoutCommon.addWidget(self.radioTimeline, 0, 1)
        layoutCommon.addWidget(self.radioText, 0, 2)
        # - Checkbox for showing IDs
        self.chkbxShowId = QCheckBox("Show IDs")
        self.chkbxShowId.setChecked(False)
        self.chkbxShowId.stateChanged.connect(self.toggleShowIds)
        layoutCommon.addWidget(self.chkbxShowId, 1, 0)

        # Layout with controls:
        self.stackControl = QStackedWidget()
        graphControls = self.createGraphControls()
        self.stackControl.addWidget(graphControls)
        timelineControls = self.createTimelineControls()
        self.stackControl.addWidget(timelineControls)
        textControls = self.createTextControls()
        self.stackControl.addWidget(textControls)
        self.stackControl.setCurrentWidget(timelineControls if self._initialPanel=="timeline" else graphControls if self._initialPanel=="graph" else textControls)
        layout.addWidget(self.stackControl)

        # Properties
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.stackControl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def createAttributesPanel(self):
        dock = QDockWidget("Properties", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Properties
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.stackControl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def createGraphControls(self):
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
        self.sliderEdgeThickness.valueChanged.connect(self.updateEdgeWidth)
        return widget

    def createTimelineControls(self):
        widget = QWidget()
        # Layout with timeline controls (empty for now):
        QVBoxLayout(widget)
        return widget

    def createTextControls(self):
        widget = QWidget()
        # Layout with text controls:
        layout = QVBoxLayout(widget)
        # - Slider for edge thickness
        layout.addWidget(QLabel("Edge thickness"))
        self.sliderEdgeThicknessText = QSlider(Qt.Horizontal)
        self.sliderEdgeThicknessText.setMinimum(1)
        self.sliderEdgeThicknessText.setMaximum(10)
        self.sliderEdgeThicknessText.setValue(2)
        layout.addWidget(self.sliderEdgeThicknessText)
        self.sliderEdgeThicknessText.valueChanged.connect(self.updateEdgeWidthText)
        # - Slider for edge label background opacity
        layout.addWidget(QLabel("Edge label opacity"))
        self.sliderEdgeLabelOpacity = QSlider(Qt.Horizontal)
        self.sliderEdgeLabelOpacity.setMinimum(0)
        self.sliderEdgeLabelOpacity.setMaximum(255)
        self.sliderEdgeLabelOpacity.setValue(220)
        layout.addWidget(self.sliderEdgeLabelOpacity)
        self.sliderEdgeLabelOpacity.valueChanged.connect(self.updateEdgeLabelOpacity)
        return widget

    def changeView(self, index):
        self.stack.setCurrentIndex(index)
        self.stackControl.setCurrentIndex(index)

    def updateEdgeWidth(self, value):
        if self.graphScene is None:
            return
        for item in self.graphScene.items():
            if isinstance(item, si.EdgeItem):
                pen = item.pen()
                pen.setWidth(value)
                item.setPen(pen)

    def updateEdgeWidthText(self, value):
        if self.textScene is None:
            return
        for item in self.textScene.items():
            if isinstance(item, si.EdgeItem):
                pen = item.pen()
                pen.setWidth(value)
                item.setPen(pen)

    def updateEdgeLabelOpacity(self, value):
        if self.textScene is None:
            return
        for item in self.textScene.items():
            if isinstance(item, txv.LaneEdgeItem):
                item._label_bg.setBrush(QBrush(QColor(255, 255, 255, value)))

    def toggleShowIds(self, state):
        for scene in (self.graphScene, self.timelineScene, self.textScene):
            if scene is None:
                continue
            for item in scene.items():
                if isinstance(item, si.NodeItem):
                    item.id_bg.setVisible(state)
                    item.id_text.setVisible(state)


def run(filepath=None):
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    model = None
    if filepath is not None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        graph = Graph.Graph(time_ml_string=content)
        tlex = TLEX.TLEX(graph=graph)
        model = DataModel(graph, tlex)
    window = MainWindow()
    if model is not None:
        window.loadModel(model, filepath)
    window.show()
    app.exec()


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else None)
