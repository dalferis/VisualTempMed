from tkinter import SE
import sceneItems as si
import graphView as gv
import timelineView as tlv
import textView as txv
from dataModel import DataModel
from pytlex_core.data import Graph, Instance, TimeX
from pytlex_core.algorithms import TLEX, Partitioner
from lxml import etree
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QCheckBox, QSlider, QRadioButton, QButtonGroup, QGridLayout, QFormLayout,
    QSizePolicy, QFileDialog, QMessageBox
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
        self._model = None
        self._eventComments = {}
        self._instanceComments = {}
        self._timexComments = {}

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.createMenuBar()
        self.createControlPanel()
        self.createAttributesPanel()
        self.statusLabel = QLabel("No file loaded")
        self.statusBar().addPermanentWidget(self.statusLabel, 1)
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
        legendAction = QAction("&Legend", self)
        legendAction.triggered.connect(self.showLegend)
        helpMenu.addAction(legendAction)
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

    def showLegend(self):
        html = """
        <h3 style="margin-top: 0;">Legend</h3>
        <p><b>Nodes</b></p>
        <table cellpadding="4" cellspacing="0">
          <tr>
            <td style="background-color: #c0c0c0; border: 1px solid black; min-width: 40px;">&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>&nbsp;EVENT (instance)</td>
          </tr>
          <tr>
            <td style="background-color: #c8e6c9; border: 1px solid black; min-width: 40px;">&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>&nbsp;TIMEX3</td>
          </tr>
        </table>
        <p><b>Edges</b></p>
        <table cellpadding="4" cellspacing="0">
          <tr>
            <td><span style="color: black;">&#9473;&#9473;&#9473;&#9473;&#9473;</span></td>
            <td>&nbsp;TLINK (temporal link)</td>
          </tr>
          <tr>
            <td><span style="color: red;">&#9473;&#9473;&#9473;&#9473;&#9473;</span></td>
            <td>&nbsp;SLINK (subordination link)</td>
          </tr>
          <tr>
            <td><span style="color: blue;">&#9473;&#9473;&#9473;&#9473;&#9473;</span></td>
            <td>&nbsp;ALINK (aspectual link)</td>
          </tr>
        </table>
        <p><b>Timeline lanes</b></p>
        <table cellpadding="4" cellspacing="0">
          <tr>
            <td><span style="color: black;">&#9473;&#9473;&#9473;&#9473;&#9473;</span></td>
            <td>&nbsp;Main partition</td>
          </tr>
          <tr>
            <td><span style="color: gray;">&#9476;&#9476;&#9476;&#9476;&#9476;</span></td>
            <td>&nbsp;Subordinate partition</td>
          </tr>
        </table>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Legend")
        msg.setTextFormat(Qt.RichText)
        msg.setText(html)
        msg.exec()

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
        self._model = model
        self._extractComments(getattr(model.graph(), "time_ml_data", None) or "")
        self.graphView = gv.GraphView(model)
        self.graphScene = self.graphView.scene
        self.timelineView = tlv.TimelineView(model)
        self.timelineScene = self.timelineView.scene
        self.textView = txv.TextView(model)
        self.textScene = self.textView.scene
        for scene in (self.graphScene, self.timelineScene, self.textScene):
            scene.nodeClicked.connect(self.showNodeAttributes)
        self.stack.addWidget(self.graphView)
        self.stack.addWidget(self.timelineView)
        self.stack.addWidget(self.textView)
        self.stack.setCurrentIndex(currentIndex)
        self.toggleShowIds(self.chkbxShowId.isChecked())
        self.clearAttributes()
        self.statusLabel.setText(filepath if filepath else "")

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
        dock = QDockWidget("Attributes", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        panel.setFixedWidth(260)
        layout = QVBoxLayout(panel)
        self.attributesTitle = QLabel("")
        self.attributesTitle.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.attributesTitle)
        self.attributesForm = QFormLayout()
        self.attributesForm.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.attributesForm.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.addLayout(self.attributesForm)
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def clearAttributes(self):
        self.attributesTitle.setText("")
        while self.attributesForm.rowCount() > 0:
            self.attributesForm.removeRow(0)

    def showNodeAttributes(self, node_id):
        self.clearAttributes()
        if self._model is None:
            return
        node = self._model.graph().nodes.get(node_id)
        if node is None:
            return
        if isinstance(node, Instance.Instance):
            event = self._model.graph().events.get(node.event)
            event_comment = self._eventComments.get(node.event)
            instance_comment = self._instanceComments.get(node.get_id_str())
            attrs = [
                ("eiid", node.get_id_str()),
                ("eventID", node.event),
                ("class", node.event_class),
                ("stem", event.stem if event is not None else None),
                ("tense", node.tense),
                ("aspect", node.aspect),
                ("pos", node.pos),
                ("polarity", node.polarity),
                ("modality", node.modality),
                ("signal", node.signal),
                ("cardinality", node.cardinality),
            ]
            if event_comment is not None:
                attrs.append(("comment (event)", event_comment))
            if instance_comment is not None:
                attrs.append(("comment (instance)", instance_comment))
            self.attributesTitle.setText(f"EVENT {node.get_id_str()}")
        elif isinstance(node, TimeX.TimeX):
            timex_comment = self._timexComments.get(node.get_id_str())
            attrs = [
                ("tid", node.get_id_str()),
                ("type", node.type),
                ("value", node.value),
                ("phrase", node.phrase),
                ("temporalFunction", node.temporalFunction),
                ("functionInDocument", node.documentFunction),
                ("mod", node.mod),
                ("anchorID", node.anchorID),
                ("beginPoint", node.beginPoint),
                ("endPoint", node.endPoint),
                ("quant", node.quant),
                ("freq", node.freq),
            ]
            if timex_comment is not None:
                attrs.append(("comment", timex_comment))
            self.attributesTitle.setText(f"TIMEX3 {node.get_id_str()}")
        else:
            return
        for key, value in attrs:
            display = "" if value is None else str(value)
            keyLabel = QLabel(f"{key}:")
            keyLabel.setWordWrap(True)
            valueLabel = QLabel(display)
            valueLabel.setWordWrap(True)
            self.attributesForm.addRow(keyLabel, valueLabel)

    def _extractComments(self, tml):
        """
        Parses raw TimeML and populates per-element comment maps.
        pytlex_core does not parse the @comment attribute, so we read it directly.
        Keys use pytlex_core's node_id convention:
          - EVENT     -> "e<n>"     (matches @eid value)
          - TIMEX3    -> "t<n>"     (matches @tid value)
          - MAKEINSTANCE -> "eiid<n>" (translated from @eiid="ei<n>")
        """
        self._eventComments = {}
        self._instanceComments = {}
        self._timexComments = {}
        if not tml:
            return
        try:
            root = etree.fromstring(tml.encode('utf-8'))
        except etree.XMLSyntaxError:
            return
        for ev in root.iter('EVENT'):
            c = ev.get('comment')
            eid = ev.get('eid')
            if c and eid:
                self._eventComments[eid] = c
        for tx in root.iter('TIMEX3'):
            c = tx.get('comment')
            tid = tx.get('tid')
            if c and tid:
                self._timexComments[tid] = c
        for mi in root.iter('MAKEINSTANCE'):
            c = mi.get('comment')
            eiid = mi.get('eiid')
            if c and eiid and eiid.startswith('ei'):
                self._instanceComments[f"eiid{eiid[2:]}"] = c

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
