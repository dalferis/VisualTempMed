import re
import sceneItems as si
from pytlex_core.data import Instance, TimeX
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, Signal


class TextView(QGraphicsView):
    def __init__(self, model):
        self.scene = TextScene(model)
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


LaneEdgeItem = si.LaneEdgeItem  # re-export for backwards compatibility


class TextScene(QGraphicsScene):
    nodeClicked = Signal(str)
    edgeClicked = Signal(object)
    selectionCleared = Signal()

    _max_line_width = 1200
    _text_height = 26
    _gutter_height = 28
    _word_spacing = 5
    _left_margin = 10
    _top_margin = 30
    _rail_x = 1260           # x of the edge routing rail (right side, beyond _max_line_width=1200)

    _track_spacing = 5
    _gutter_padding = 5

    _DCT_PADDING = 4
    _DCT_BG = QColor(240, 240, 250)
    _DCT_FG = Qt.darkBlue

    _EVENT_RE = re.compile(r'<EVENT\b([^>]*)>([\s\S]*?)</EVENT>', re.IGNORECASE)
    _TIMEX_RE = re.compile(r'<TIMEX3\b([^>]*)>([\s\S]*?)</TIMEX3>', re.IGNORECASE)
    _ANY_TAG_RE = re.compile(r'</?[A-Za-z][^>]*>')
    _EID_RE = re.compile(r'eid="(e\d+)"', re.IGNORECASE)
    _TID_RE = re.compile(r'tid="(t\d+)"', re.IGNORECASE)
    _INNER_TAG_RE = re.compile(r'<[^>]+>')
    _LINE_BREAK_TAGS = {'</s>', '</turn>', '</p>', '</section>', '</br>', '<br>', '<br/>'}

    @property
    def line_height(self):
        return self._text_height + self._gutter_height

    def __init__(self, dataModel):
        super().__init__()
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self._lines = []
        self._highlighted_edges = []
        self._font = QFont()
        self._font.setPointSize(11)
        self._font.setBold(True)  # free text rendered in bold
        self._dct_label = None
        self._dct_text_rect = None
        self._dct_rect = None
        self.createScene()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        clicked = None
        for it in self.items(event.scenePos()):
            owner = self._enclosingTarget(it)
            if owner is not None:
                clicked = owner
                break
        self._clearHighlights()
        if isinstance(clicked, LaneEdgeItem):
            clicked.setHighlighted(True)
            self._highlighted_edges = [clicked]
            self.edgeClicked.emit(clicked.link)
        elif isinstance(clicked, si.NodeItem):
            self._highlightNodeOutgoing(clicked)
            self.nodeClicked.emit(clicked.node_id)
        else:
            self.selectionCleared.emit()

    def _highlightNodeOutgoing(self, node):
        outgoing = [e for e in self.items()
                    if isinstance(e, LaneEdgeItem) and e.source is node]
        for e in outgoing:
            e.setHighlighted(True)
        self._highlighted_edges = outgoing

    def selectNode(self, node_id):
        """Apply the same highlight a click would, without emitting nodeClicked.
        Used by MainWindow to carry the selection across view switches."""
        self._clearHighlights()
        self.clearSelection()
        node = self.nodes.get(node_id) if node_id is not None else None
        if node is not None:
            node.setSelected(True)
            self._highlightNodeOutgoing(node)

    def selectEdge(self, link):
        """Highlight the edge backed by the given Link object, without
        emitting edgeClicked. Used by MainWindow to carry the selection
        across view switches."""
        self._clearHighlights()
        self.clearSelection()
        if link is None:
            return
        for it in self.items():
            if isinstance(it, LaneEdgeItem) and it.link is link:
                it.setHighlighted(True)
                self._highlighted_edges = [it]
                return

    @staticmethod
    def _enclosingTarget(item):
        while item is not None:
            if isinstance(item, (LaneEdgeItem, si.NodeItem)):
                return item
            item = item.parentItem()
        return None

    def _clearHighlights(self):
        for e in self._highlighted_edges:
            e.setHighlighted(False)
        self._highlighted_edges = []

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, si.NodeItem):
            self.nodes[item.node_id] = item

    # ------- Geometry helpers (used by LaneEdgeItem) -------

    def gutterY(self, gutter_idx, track):
        if gutter_idx == 0:
            gutter_top = self._top_margin - self._gutter_height
        else:
            gutter_top = self._top_margin + (gutter_idx - 1) * self.line_height + self._text_height
        return gutter_top + self._gutter_padding + (track + 0.5) * self._track_spacing

    def railX(self, track):
        return self._rail_x + (track + 0.5) * self._track_spacing

    def lineOfNode(self, node_item):
        cy = node_item.pos().y()
        approx = (cy - self._top_margin - self._text_height / 2) / self.line_height
        return max(0, int(round(approx)))

    # ------- Domain helpers -------

    def isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def isCreationTimeLink(self, link):
        return self.isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self.isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def buildEventToNodeIdMap(self):
        mapping = {}
        for node in self._graph.nodes.values():
            if isinstance(node, Instance.Instance):
                mapping[node.event] = node.get_id_str()
        return mapping

    def stripInnerTags(self, text):
        return self._INNER_TAG_RE.sub('', text)

    def extractTextBody(self, tml):
        match = re.search(r'<TEXT\b[^>]*>([\s\S]*?)</TEXT>', tml, re.IGNORECASE)
        return match.group(1) if match else tml

    # ------- Layout -------

    def _ensureLine(self, line_idx):
        while len(self._lines) <= line_idx:
            self._lines.append([])

    def addWord(self, word, x, y, line_idx):
        text_item = QGraphicsTextItem(si.decodeText(word))
        text_item.setFont(self._font)
        rect = text_item.boundingRect()
        if x + rect.width() > self._max_line_width and x > self._left_margin:
            x = self._left_margin
            y += self.line_height
            line_idx += 1
        text_item.setPos(x, y + (self._text_height - rect.height()) / 2)
        self.addItem(text_item)
        self._ensureLine(line_idx)
        self._lines[line_idx].append(text_item)
        x += rect.width() + self._word_spacing
        return x, y, line_idx

    def addNodeInline(self, node_id, text, x, y, line_idx):
        node = si.NodeItem(node_id, text=text)
        node.setFlag(QGraphicsItem.ItemIsMovable, False)
        rect = node.boundingRect()
        w = rect.width()
        if x + w > self._max_line_width and x > self._left_margin:
            x = self._left_margin
            y += self.line_height
            line_idx += 1
        node.setPos(x + w / 2, y + self._text_height / 2)
        self.addItem(node)
        self._ensureLine(line_idx)
        self._lines[line_idx].append(node)
        x += w + self._word_spacing
        return x, y, line_idx

    def newLine(self, x, y, line_idx):
        return self._left_margin, y + self.line_height, line_idx + 1

    def renderTextChunk(self, chunk, x, y, line_idx):
        for word in chunk.split():
            x, y, line_idx = self.addWord(word, x, y, line_idx)
        return x, y, line_idx

    def layoutText(self, body, eid_to_node_id):
        x = self._left_margin
        y = self._top_margin
        line_idx = 0
        # Drop trailing whitespace and CR/LF entities so they don't emit empty trailing lines
        body = body.rstrip()
        while body.endswith('&#13;') or body.endswith('&#10;'):
            body = body[:-5].rstrip()
        pos = 0
        n = len(body)

        while pos < n:
            ch = body[pos]

            if ch.isspace():
                pos += 1
                continue

            if body.startswith('&#13;', pos) or body.startswith('&#10;', pos):
                x, y, line_idx = self.newLine(x, y, line_idx)
                pos += 5
                continue

            if ch == '<':
                event_match = self._EVENT_RE.match(body, pos)
                if event_match:
                    eid_m = self._EID_RE.search(event_match.group(1))
                    inner = si.decodeText(self.stripInnerTags(event_match.group(2)).strip()) or "?"
                    if eid_m and eid_m.group(1) in eid_to_node_id:
                        x, y, line_idx = self.addNodeInline(eid_to_node_id[eid_m.group(1)], inner, x, y, line_idx)
                    else:
                        x, y, line_idx = self.renderTextChunk(inner, x, y, line_idx)
                    pos = event_match.end()
                    continue

                timex_match = self._TIMEX_RE.match(body, pos)
                if timex_match:
                    tid_m = self._TID_RE.search(timex_match.group(1))
                    inner = si.decodeText(self.stripInnerTags(timex_match.group(2)).strip()) or "?"
                    placed = False
                    if tid_m:
                        tid = tid_m.group(1)
                        timex_node = self._graph.nodes.get(tid)
                        if timex_node is not None and not self.isCreationTimeTimex3(timex_node):
                            x, y, line_idx = self.addNodeInline(tid, inner, x, y, line_idx)
                            placed = True
                    if not placed:
                        x, y, line_idx = self.renderTextChunk(inner, x, y, line_idx)
                    pos = timex_match.end()
                    continue

                tag_match = self._ANY_TAG_RE.match(body, pos)
                if tag_match:
                    tag_compact = re.sub(r'\s+', '', tag_match.group(0).lower().strip())
                    if tag_compact in self._LINE_BREAK_TAGS:
                        x, y, line_idx = self.newLine(x, y, line_idx)
                    pos = tag_match.end()
                    continue

                x, y, line_idx = self.addWord('<', x, y, line_idx)
                pos += 1
                continue

            word_match = re.match(r'(?:(?!&#1[03];)[^\s<])+', body[pos:])
            if word_match:
                x, y, line_idx = self.addWord(word_match.group(0), x, y, line_idx)
                pos += word_match.end()
            else:
                pos += 1

    # ------- Edge layout -------

    def _resizeGutterIfNeeded(self, max_tracks_per_gutter):
        if not max_tracks_per_gutter:
            return
        needed = max(max_tracks_per_gutter.values())
        needed_height = needed * self._track_spacing + 2 * self._gutter_padding
        if needed_height <= self._gutter_height:
            return
        old_line_height = self.line_height
        self._gutter_height = needed_height
        new_line_height = self.line_height
        if new_line_height == old_line_height:
            return
        for line_idx, items in enumerate(self._lines):
            old_line_top = self._top_margin + line_idx * old_line_height
            new_line_top = self._top_margin + line_idx * new_line_height
            shift = new_line_top - old_line_top
            if shift == 0:
                continue
            for item in items:
                p = item.pos()
                item.setPos(p.x(), p.y() + shift)

    def createScene(self):
        eid_to_node_id = self.buildEventToNodeIdMap()
        tml = getattr(self._graph, "time_ml_data", None) or ""
        body = self.extractTextBody(tml)
        self.layoutText(body, eid_to_node_id)
        si.LaneEdgePlanner(self, track_spacing=self._track_spacing,
                           gutter_padding=self._gutter_padding).drawEdges()
        self._prepareDctOverlay()

    def _prepareDctOverlay(self):
        dct = next((n for n in self._graph.nodes.values() if self.isCreationTimeTimex3(n)), None)
        if dct is None:
            return
        value = getattr(dct, "value", None) or "?"
        phrase = getattr(dct, "phrase", None)
        label = f"Document Creation Time: {value}"
        if phrase and phrase != value:
            label += f" ({phrase})"
        fm = QFontMetrics(self._font)
        text_rect = fm.boundingRect(label)
        w = text_rect.width() + 2 * self._DCT_PADDING
        h = text_rect.height() + 2 * self._DCT_PADDING
        x = self._left_margin
        y = self._top_margin - self._gutter_height - h - 5
        self._dct_label = label
        self._dct_text_rect = text_rect
        self._dct_rect = QRectF(x, y, w, h)
        # Drawn via drawForeground (not as a scene item), so we must extend
        # sceneRect manually to keep the box reachable when scrolling.
        self.setSceneRect(self.itemsBoundingRect().united(self._dct_rect).adjusted(-10, -10, 10, 10))

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self._dct_rect is None or not rect.intersects(self._dct_rect):
            return
        painter.save()
        painter.setBrush(QBrush(self._DCT_BG))
        painter.setPen(QPen(self._DCT_FG, 1))
        painter.drawRect(self._dct_rect)
        painter.setPen(self._DCT_FG)
        painter.setFont(self._font)
        painter.drawText(self._dct_rect.x() + self._DCT_PADDING - self._dct_text_rect.left(),
                         self._dct_rect.y() + self._DCT_PADDING - self._dct_text_rect.top(),
                         self._dct_label)
        painter.restore()
