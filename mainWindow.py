from detector import FileFormat, detectFormatContent
from converter import convertContent
import validator
import dateLinks
import sceneItems as si
import timeView as tv
import textView as txv
from dataModel import DataModel
from pytlex_core.data import Graph, Instance, TimeX
from pytlex_core.algorithms import TLEX, Partitioner
from lxml import etree
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QStackedWidget,
    QLabel, QCheckBox, QSlider, QRadioButton, QButtonGroup, QGridLayout, QFormLayout,
    QSizePolicy, QFileDialog, QMessageBox, QTextEdit, QDialog, QDialogButtonBox,
    QPushButton
)

class _StableWidthPanel(QWidget):
    """Widget that reports a fixed width as sizeHint so its parent
    QDockWidget does not reflow when the inner layout's content changes.
    Height still tracks the layout. The user can still resize the dock
    manually via its border."""
    def __init__(self, hint_width):
        super().__init__()
        self._hint_width = hint_width
    def sizeHint(self):
        return QSize(self._hint_width, super().sizeHint().height())


class MainWindow(QMainWindow):
    _initialPanel = "time"

    def __init__(self, model=None):
        super().__init__()

        self.setWindowTitle("Medical Timeline Visualizer")
        self.resize(1200, 800)

        self.timeView = self.timeScene = None
        self.textView = self.textScene = None
        self._model = None
        self._selectedNodeId = None
        self._selectedLink = None
        self._currentPath = None
        self._inferDateOrder = True   # infer chronological order from TIMEX3 dates
        self._eventComments = {}
        self._instanceComments = {}
        self._timexComments = {}

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.createControlPanel()
        self.createAttributesPanel()
        self.createMenuBar()
        self.statusLabel = QLabel("No file loaded")
        self.statusLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
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

        convertMenu = menuBar.addMenu("&Tools")
        convertAction = QAction("Convert &E3C file to TimeML", self)
        convertAction.triggered.connect(self.convertE3cFile)
        convertMenu.addAction(convertAction)
        validateAction = QAction("&Validate TimeML file", self)
        validateAction.triggered.connect(self.validateTimeMlFile)
        convertMenu.addAction(validateAction)

        optionsMenu = menuBar.addMenu("&Options")
        self.dateOrderAction = QAction("Infer order from TIMEX3 &dates", self)
        self.dateOrderAction.setCheckable(True)
        self.dateOrderAction.setChecked(self._inferDateOrder)
        self.dateOrderAction.toggled.connect(self.toggleDateOrder)
        optionsMenu.addAction(self.dateOrderAction)

        viewMenu = menuBar.addMenu("&View")
        controlAction = self.controlDock.toggleViewAction()
        controlAction.setText("&Control panel")
        viewMenu.addAction(controlAction)
        attributesAction = self.attributesDock.toggleViewAction()
        attributesAction.setText("&Attributes panel")
        viewMenu.addAction(attributesAction)

        helpMenu = menuBar.addMenu("&Help")
        usageAction = QAction("&Usage", self)
        usageAction.setShortcut("F1")
        usageAction.triggered.connect(self.showUsage)
        helpMenu.addAction(usageAction)
        legendAction = QAction("&Legend", self)
        legendAction.triggered.connect(self.showLegend)
        helpMenu.addAction(legendAction)
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)

    def openTimeMlFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open TimeML or E3C file", "", "TimeML/E3C files (*.tml *.xml);;All files (*)")
        if not path:
            return
        self._loadPath(path)

    def _loadPath(self, path):
        """Reads/converts a TimeML or E3C file, builds the model (optionally
        adding date-inferred ordering links), and loads it. Used by Open... and
        by the Options toggle to re-render the current file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            fileFormat = detectFormatContent(content)
            if fileFormat == FileFormat.E3C:
                result = convertContent(content)
                if not result[0]:
                    QMessageBox.critical(self, "Error", "E3C -> TimeML conversion failed:\n" + "\n".join(str(e) for e in result[1:]))
                    return
                content = result[1]
            elif fileFormat != FileFormat.TML:
                QMessageBox.critical(self, "Error", "The selected file is not a TimeML or E3C file.")
                return
            model = self._buildModel(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{e}")
            return
        self._currentPath = path
        self.loadModel(model, path)

    def _buildModel(self, content):
        graph = Graph.Graph(time_ml_string=content)
        # Optionally infer chronological ordering links from TIMEX3 dates and
        # add them BEFORE partitioning, so TLEX merges partitions they connect.
        if self._inferDateOrder:
            for link in dateLinks.infer_date_links(graph):
                graph.links[link.get_id_str()] = link
        # Reset pytlex_core's module-level SLink set (it leaks across calls,
        # and infer_date_links built a throwaway TLEX above).
        Partitioner.single_links.clear()
        tlex = TLEX.TLEX(graph=graph)
        # Merge Connectivity_Increaser's suggested TLINKs into graph.links
        # so downstream consumers (validator, JSON export, attribute panel)
        # see them as first-class links. timeView still distinguishes them
        # visually because the planner reads tlex.suggested_links separately
        # and marks plan['suggested']=True (dashed pen).
        for link in tlex.suggested_links or []:
            graph.links.setdefault(link.get_id_str(), link)
        return DataModel(graph, tlex)

    def convertE3cFile(self):
        in_path, _ = QFileDialog.getOpenFileName(self, "Select E3C file to convert", "", "E3C files (*.xml);;All files (*)")
        if not in_path:
            return
        try:
            with open(in_path, 'r', encoding='utf-8') as f:
                content = f.read()
            fileFormat = detectFormatContent(content)
            if fileFormat != FileFormat.E3C:
                QMessageBox.critical(self, "Error", f"The selected file is not an E3C file (detected: {fileFormat.name}).")
                return
            result = convertContent(content)
            if not result[0]:
                QMessageBox.critical(self, "Error", "E3C -> TimeML conversion failed:\n" + "\n".join(str(e) for e in result[1:]))
                return
            tml_content = result[1]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not convert file:\n{e}")
            return
        default_out = in_path + ".tml"
        out_path, _ = QFileDialog.getSaveFileName(self, "Save TimeML file", default_out, "TimeML files (*.tml);;All files (*)")
        if not out_path:
            return
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(tml_content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not write file:\n{e}")
            return
        QMessageBox.information(self, "Conversion complete", f"File converted successfully:\n{out_path}")

    def validateTimeMlFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select TimeML file to validate", "", "TimeML files (*.tml);;All files (*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            result = validator.validateContent(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not validate file:\n{e}")
            return
        if result[0]:
            msg = QMessageBox(self)
            msg.setWindowTitle("Validation")
            msg.setIcon(QMessageBox.Information)
            msg.setText(f"The file \"{path}\" is valid TimeML (XSD and TimeML spec).")
            msg.exec()
        else:
            # A plain resizable dialog (not QMessageBox, which re-applies a
            # fixed size and ignores the resize grip) so the error list can be
            # enlarged by dragging the window edges.
            self._showValidationErrors(path, "\n".join(str(e) for e in result[1:]))

    def _showValidationErrors(self, path, errors):
        dlg = QDialog(self)
        dlg.setWindowTitle("Validation")
        dlg.resize(680, 440)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(f"The file \"{path}\" is NOT valid TimeML:"))
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setLineWrapMode(QTextEdit.NoWrap)
        edit.setPlainText(errors)
        layout.addWidget(edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        dlg.exec()

    def toggleDateOrder(self, checked):
        self._inferDateOrder = checked
        if self._currentPath:
            self._loadPath(self._currentPath)

    def showAbout(self):
        QMessageBox.about(
            self,
            "About",
            "Visualizador de líneas temporales en contexto médico\n\nPFG Ingeniería Informática\n\nUniversidad Nacional de Educación a Distancia\n\n2026\n\nDavid Alvarez Feliciano"
        )

    def showUsage(self):
        html = """
        <h3 style="margin-top: 0;">Usage</h3>
        <p><b>Opening a file</b></p>
        <ul>
          <li><i>File &gt; Open TimeML file...</i> (Ctrl+O) loads a TimeML <code>.tml</code> or E3C <code>.xml</code> file.</li>
          <li>E3C files are detected and converted to TimeML automatically.</li>
        </ul>
        <p><b>Choosing a view</b></p>
        <ul>
          <li><b>Time</b>: nodes and links laid out as a graph; events are ordered left-to-right chronologically and simultaneous events stack vertically.</li>
          <li><b>Text</b>: source text with inline annotations and routed edges.</li>
        </ul>
        <p><b>Inspecting an annotated text</b></p>
        <ul>
          <li>In any view, click a node to display its attributes in the right panel.</li>
          <li>In the Time view, nodes can be moved by dragging them with the mouse.</li>
          <li>In the Text view, clicking a node also highlights its outgoing edges.</li>
          <li>In the Text view, click an edge to highlight it; click empty space to clear.</li>
          <li>TLINKs to/from the Document Creation Time appear in the Attributes panel of the involved node, prefixed with <code>-&gt; DCT</code> or <code>&lt;- DCT</code>.</li>
        </ul>
        <p><b>Navigation</b></p>
        <ul>
          <li>Zoom in / out: Ctrl + mouse wheel, or use the <i>Zoom in</i> / <i>Zoom out</i> / <i>Reset zoom</i> buttons in the Control panel.</li>
          <li>Vertical scroll: mouse wheel or vertical bar.</li>
          <li>Horizontal scroll: horizontal bar.</li>
        </ul>
        <p><b>Control panel</b></p>
        <ul>
          <li><i>Show IDs</i>: toggles internal identifiers on nodes.</li>
          <li><i>Zoom in</i> / <i>Zoom out</i> / <i>Reset zoom</i>: zoom controls for the active view.</li>
          <li><i>Edge thickness</i>: adjusts edge line width.</li>
          <li><i>Edge label opacity</i>: background opacity of edge labels.</li>
        </ul>
        <p><b>View menu</b></p>
        <ul>
          <li>Toggle visibility of the Control and Attributes panels.</li>
        </ul>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Usage")
        msg.setTextFormat(Qt.RichText)
        msg.setText(html)
        msg.exec()

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
            <td><span style="color: black; font-family: monospace; font-size: 14pt;">&#9472;&#9472;&#9472;&#9472;&#9472;</span></td>
            <td>&nbsp;TLINK (annotated temporal link)</td>
          </tr>
          <tr>
            <td><span style="color: black; font-family: monospace; font-size: 14pt;">&#8211;&nbsp;&#8211;&nbsp;&#8211;&nbsp;&#8211;</span></td>
            <td>&nbsp;TLINK (suggested temporal link)</td>
          </tr>
          <tr>
            <td><span style="color: #960096; font-family: monospace; font-size: 14pt;">&#8211;&#183;&#8211;&#183;&#8211;&#183;&#8211;&#183;</span></td>
            <td>&nbsp;TLINK (inferred from TIMEX3 dates)</td>
          </tr>
          <tr>
            <td><span style="color: red;   font-family: monospace; font-size: 14pt;">&#9472;&#9472;&#9472;&#9472;&#9472;</span></td>
            <td>&nbsp;SLINK (subordination link)</td>
          </tr>
          <tr>
            <td><span style="color: blue;  font-family: monospace; font-size: 14pt;">&#9472;&#9472;&#9472;&#9472;&#9472;</span></td>
            <td>&nbsp;ALINK (aspectual link)</td>
          </tr>
        </table>
        <p><b>Partitions</b></p>
        <p>"Main" partition holds the "real-world" facts of the document.<br>"Subordinate" partitions hang off the "Main" partitions through SLINKs.</p>
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
        for view in (self.timeView, self.textView):
            if view is None:
                continue
            self.stack.removeWidget(view)
            view.deleteLater()
        self.timeView = self.timeScene = None
        self.textView = self.textScene = None
        # Reset pytlex_core's module-level SLink set; it leaks across files:
        Partitioner.single_links.clear()
        self._model = model
        self._extractComments(getattr(model.graph(), "time_ml_data", None) or "")
        self.timeView = tv.TimeView(model)
        self.timeScene = self.timeView.scene
        self.textView = txv.TextView(model)
        self.textScene = self.textView.scene
        for scene in (self.timeScene, self.textScene):
            scene.nodeClicked.connect(self.showNodeAttributes)
            scene.edgeClicked.connect(self.onEdgeClicked)
            scene.selectionCleared.connect(self.onSelectionCleared)
        self.stack.addWidget(self.timeView)
        self.stack.addWidget(self.textView)
        self.stack.setCurrentIndex(currentIndex)
        self.toggleShowIds(self.chkbxShowId.isChecked())
        self.clearAttributes()
        self._selectedLink = None
        self.statusLabel.setText(filepath if filepath else "")

    def createControlPanel(self):
        self.controlDock = dock = QDockWidget("Control panel", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Layout with common controls:
        layoutCommon = QGridLayout()
        layout.addLayout(layoutCommon)
        # - Radio buttons for view selection
        self.radioTime = QRadioButton("Time")
        self.radioText = QRadioButton("Text")
        self.radioTime.setChecked(self._initialPanel=="time")
        self.radioText.setChecked(self._initialPanel=="text")
        self.radiogroupView = QButtonGroup(self)
        self.radiogroupView.addButton(self.radioTime)
        self.radiogroupView.addButton(self.radioText)
        self.radiogroupView.setId(self.radioTime, 0)
        self.radiogroupView.setId(self.radioText, 1)
        self.radiogroupView.idClicked.connect(self.changeView)
        layoutCommon.addWidget(self.radioTime, 0, 0)
        layoutCommon.addWidget(self.radioText, 0, 1)
        # - Checkbox for showing IDs
        self.chkbxShowId = QCheckBox("Show IDs")
        self.chkbxShowId.setChecked(False)
        self.chkbxShowId.stateChanged.connect(self.toggleShowIds)
        layoutCommon.addWidget(self.chkbxShowId, 1, 0)
        # - Zoom buttons (work on the active view; same factor as Ctrl + wheel)
        self.btnZoomOut = QPushButton("Zoom out")
        self.btnZoomOut.clicked.connect(self.zoomOut)
        layoutCommon.addWidget(self.btnZoomOut, 2, 0)
        self.btnZoomIn = QPushButton("Zoom in")
        self.btnZoomIn.clicked.connect(self.zoomIn)
        layoutCommon.addWidget(self.btnZoomIn, 2, 1)
        self.btnZoomReset = QPushButton("Reset zoom")
        self.btnZoomReset.clicked.connect(self.resetZoom)
        layoutCommon.addWidget(self.btnZoomReset, 3, 0, 1, 2)

        # Layout with controls:
        self.stackControl = QStackedWidget()
        timeControls = self.createTimeControls()
        self.stackControl.addWidget(timeControls)
        textControls = self.createTextControls()
        self.stackControl.addWidget(textControls)
        self.stackControl.setCurrentWidget(timeControls if self._initialPanel=="time" else textControls)
        layout.addWidget(self.stackControl)

        # Properties
        layout.addStretch()
        dock.setWidget(panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.stackControl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def createAttributesPanel(self):
        self.attributesDock = dock = QDockWidget("Attributes", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = _StableWidthPanel(260)
        panel.setMinimumWidth(200)
        font = panel.font()
        font.setPointSize(font.pointSize() + 1)
        panel.setFont(font)
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
        self._selectedNodeId = None

    def onEdgeClicked(self, link):
        self.clearAttributes()
        self._selectedLink = link

    def onSelectionCleared(self):
        self.clearAttributes()
        self._selectedLink = None

    def showNodeAttributes(self, node_id):
        self.clearAttributes()
        if self._model is None:
            return
        node = self._model.graph().nodes.get(node_id)
        if node is None:
            return
        self._selectedNodeId = node_id
        self._selectedLink = None
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
        attrs.extend(self._dctTlinkAttrs(node_id))
        for key, value in attrs:
            display = "" if value is None else str(value)
            keyLabel = QLabel(f"{key}:")
            keyLabel.setWordWrap(True)
            # Insert U+200B (zero-width space) between chars so QLabel can wrap mid-word when no space fits.
            valueLabel = QLabel('\u200B'.join(display))
            valueLabel.setWordWrap(True)
            self.attributesForm.addRow(keyLabel, valueLabel)

    def _dctTlinkAttrs(self, node_id):
        """Returns extra attribute rows for TLINKs that connect node_id with the
        Document Creation Time. TLINKs to/from DCT are not drawn in textView
        (would saturate the scene), so we surface them here instead.
        """
        graph = self._model.graph()
        dct_id = next((nid for nid, n in graph.nodes.items()
                       if isinstance(n, TimeX.TimeX)
                       and getattr(n, "documentFunction", None)
                       and n.documentFunction.upper() == "CREATION_TIME"),
                      None)
        if dct_id is None or node_id == dct_id:
            return []
        rows = []
        for link in graph.links.values():
            if link.link_tag != "TLINK":
                continue
            if getattr(link, "_date_inferred", False):
                continue   # synthetic ordering link, not an annotated relation
            if link.start_node == node_id and link.related_to_node == dct_id:
                rows.append(("-> DCT", link.rel_type))
            elif link.related_to_node == node_id and link.start_node == dct_id:
                rows.append(("<- DCT", link.rel_type))
        return rows

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

    def createTimeControls(self):
        widget = QWidget()
        # Layout with time view controls:
        layout = QVBoxLayout(widget)
        # - Slider for edge thickness
        layout.addWidget(QLabel("Edge thickness"))
        self.sliderEdgeThickness = QSlider(Qt.Horizontal)
        self.sliderEdgeThickness.setMinimum(1)
        self.sliderEdgeThickness.setMaximum(10)
        self.sliderEdgeThickness.setValue(2)
        layout.addWidget(self.sliderEdgeThickness)
        self.sliderEdgeThickness.valueChanged.connect(self.updateEdgeWidth)
        # - Slider for edge label background opacity
        layout.addWidget(QLabel("Edge label opacity"))
        self.sliderEdgeLabelOpacity = QSlider(Qt.Horizontal)
        self.sliderEdgeLabelOpacity.setMinimum(0)
        self.sliderEdgeLabelOpacity.setMaximum(255)
        self.sliderEdgeLabelOpacity.setValue(220)
        layout.addWidget(self.sliderEdgeLabelOpacity)
        self.sliderEdgeLabelOpacity.valueChanged.connect(self.updateEdgeLabelOpacity)
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
        self.sliderEdgeLabelOpacityText = QSlider(Qt.Horizontal)
        self.sliderEdgeLabelOpacityText.setMinimum(0)
        self.sliderEdgeLabelOpacityText.setMaximum(255)
        self.sliderEdgeLabelOpacityText.setValue(220)
        layout.addWidget(self.sliderEdgeLabelOpacityText)
        self.sliderEdgeLabelOpacityText.valueChanged.connect(self.updateEdgeLabelOpacityText)
        return widget

    def zoomIn(self):
        view = self.stack.currentWidget()
        if view is None:
            return
        view.scale(1.15, 1.15)

    def zoomOut(self):
        view = self.stack.currentWidget()
        if view is None:
            return
        view.scale(1 / 1.15, 1 / 1.15)

    def resetZoom(self):
        view = self.stack.currentWidget()
        if view is None:
            return
        view.resetTransform()

    def changeView(self, index):
        self.stack.setCurrentIndex(index)
        self.stackControl.setCurrentIndex(index)
        active_scene = self.timeScene if index == 0 else self.textScene
        if active_scene is None:
            return
        if self._selectedNodeId is not None:
            active_scene.selectNode(self._selectedNodeId)
        elif self._selectedLink is not None:
            active_scene.selectEdge(self._selectedLink)

    def updateEdgeWidth(self, value):
        if self.timeScene is None:
            return
        for item in self.timeScene.items():
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
        if self.timeScene is None:
            return
        for item in self.timeScene.items():
            if isinstance(item, si.LaneEdgeItem):
                item._label_bg.setBrush(QBrush(QColor(255, 255, 255, value)))

    def updateEdgeLabelOpacityText(self, value):
        if self.textScene is None:
            return
        for item in self.textScene.items():
            if isinstance(item, si.LaneEdgeItem):
                item._label_bg.setBrush(QBrush(QColor(255, 255, 255, value)))

    def toggleShowIds(self, state):
        for scene in (self.timeScene, self.textScene):
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
    window = MainWindow()
    if filepath is not None:
        window._loadPath(filepath)
    window.show()
    app.exec()


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else None)
