import re
import sceneItems as si
from pytlex_core.data import Instance, TimeX
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QRectF


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


class TextScene(si.SelectableScene):
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

    # Header boxes for TIMEX3s with a functionInDocument other than NONE
    # (CREATION_TIME, PUBLICATION_TIME, ...). Each function gets its own colour.
    _DOC_FUNCTION_TITLES = {
        "CREATION_TIME": "Document Creation Time",
        "PUBLICATION_TIME": "Publication Time",
        "MODIFICATION_TIME": "Modification Time",
        "RELEASE_TIME": "Release Time",
        "RECEPTION_TIME": "Reception Time",
        "EXPIRATION_TIME": "Expiration Time",
    }
    _DOC_FUNCTION_COLORS = {
        "CREATION_TIME": QColor(0, 0, 139),        # dark blue
        "PUBLICATION_TIME": QColor(0, 110, 0),     # dark green
        "MODIFICATION_TIME": QColor(139, 0, 139),  # dark magenta
        "RELEASE_TIME": QColor(180, 95, 0),        # dark orange
        "RECEPTION_TIME": QColor(0, 130, 130),     # dark cyan
        "EXPIRATION_TIME": QColor(150, 0, 0),      # dark red
    }
    _DOC_FUNCTION_DEFAULT_COLOR = QColor(60, 60, 60)

    _EVENT_RE = re.compile(r'<EVENT\b([^>]*)>([\s\S]*?)</EVENT>', re.IGNORECASE)
    _TIMEX_RE = re.compile(r'<TIMEX3\b([^>]*)>([\s\S]*?)</TIMEX3>', re.IGNORECASE)
    _ANY_TAG_RE = re.compile(r'</?[A-Za-z][^>]*>')
    _EID_RE = re.compile(r'eid="(e\d+)"', re.IGNORECASE)
    _TID_RE = re.compile(r'tid="(t\d+)"', re.IGNORECASE)
    _INNER_TAG_RE = re.compile(r'<[^>]+>')
    _LINE_BREAK_TAGS = {'</s>', '</turn>', '</p>', '</section>', '</br>', '<br>', '<br/>'}

    @property
    def _line_height(self):
        return self._text_height + self._gutter_height

    def __init__(self, dataModel):
        super().__init__(dataModel)
        self._lines = []
        # Per-line extra height contributed by stacked MAKEINSTANCE satellites
        # under a multi-instance EVENT. Lines with satellites push subsequent
        # text rows further down so the edge gutter stays below the stack
        # (otherwise satellites would occlude edges routed through the gutter).
        self._line_extra_height = {}
        self._font = QFont()
        self._font.setPointSize(11)
        self._font.setBold(True)  # free text rendered in bold
        # Header overlay boxes: list of (QRectF, label, text_rect, QColor).
        self._doc_function_boxes = []
        self._createScene()

    # ------- Geometry helpers (used by LaneEdgeItem and LaneEdgePlanner) -------

    def gutterY(self, gutter_idx, track):
        if gutter_idx == 0:
            gutter_top = self._top_margin - self._gutter_height
        else:
            # Cumulative extras shift the gutter down by the total satellite
            # height of every preceding line.
            cum = sum(self._line_extra_height.get(i, 0) for i in range(gutter_idx))
            gutter_top = (self._top_margin + (gutter_idx - 1) * self._line_height
                          + self._text_height + cum)
        return gutter_top + self._gutter_padding + (track + 0.5) * self._track_spacing

    def railX(self, track):
        return self._rail_x + (track + 0.5) * self._track_spacing

    def lineOfNode(self, node_item):
        # When lines have variable height (because of stacked satellites)
        # the cy/line_height formula no longer holds. Use the line index
        # stamped on each node by addNodeInline / addStackedSatellite.
        return getattr(node_item, '_line_idx', 0)

    # ------- Domain helpers -------

    def _isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def _isDocumentFunctionTimex3(self, timex3):
        """True for any TIMEX3 acting as a document reference time
        (functionInDocument other than NONE): CREATION_TIME,
        PUBLICATION_TIME, etc. These are shown in the header overlay."""
        if not isinstance(timex3, TimeX.TimeX) or not getattr(timex3, "documentFunction", None):
            return False
        return timex3.documentFunction.upper() != "NONE"

    def isCreationTimeLink(self, link):
        return self._isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self._isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def _buildEventToNodeIdsMap(self):
        """Returns dict[eid, list[eiid]]. A single EVENT can have multiple
        MAKEINSTANCE entries (different temporal/modal realizations of the
        same predicate, e.g. e12 with both ei340 and ei354 in
        APW19980213.1320.tml). All of them need NodeItems in the scene so
        their edges are drawable; otherwise edges that target the
        non-rendered instances silently disappear from textView."""
        mapping = {}
        for node in self._graph.nodes.values():
            if isinstance(node, Instance.Instance):
                mapping.setdefault(node.event, []).append(node.get_id_str())
        return mapping

    def _stripInnerTags(self, text):
        return self._INNER_TAG_RE.sub('', text)

    def _extractTextBody(self, tml):
        match = re.search(r'<TEXT\b[^>]*>([\s\S]*?)</TEXT>', tml, re.IGNORECASE)
        return match.group(1) if match else tml

    # ------- Layout -------

    def _ensureLine(self, line_idx):
        while len(self._lines) <= line_idx:
            self._lines.append([])

    def _advanceY(self, y, line_idx):
        """Y advance from one line to the next, accounting for any extra
        height contributed by stacked satellites on the line we are
        leaving behind."""
        return y + self._line_height + self._line_extra_height.get(line_idx, 0)

    def _addWord(self, word, x, y, line_idx):
        text_item = QGraphicsTextItem(si.decodeText(word))
        text_item.setFont(self._font)
        rect = text_item.boundingRect()
        if x + rect.width() > self._max_line_width and x > self._left_margin:
            x = self._left_margin
            y = self._advanceY(y, line_idx)
            line_idx += 1
        text_item.setPos(x, y + (self._text_height - rect.height()) / 2)
        self.addItem(text_item)
        self._ensureLine(line_idx)
        self._lines[line_idx].append(text_item)
        x += rect.width() + self._word_spacing
        return x, y, line_idx

    def _addNodeInline(self, node_id, text, x, y, line_idx):
        node = si.NodeItem(node_id, text=text)
        node.setFlag(QGraphicsItem.ItemIsMovable, False)
        rect = node.boundingRect()
        w = rect.width()
        if x + w > self._max_line_width and x > self._left_margin:
            x = self._left_margin
            y = self._advanceY(y, line_idx)
            line_idx += 1
        node.setPos(x + w / 2, y + self._text_height / 2)
        node._line_idx = line_idx
        self.addItem(node)
        self._ensureLine(line_idx)
        self._lines[line_idx].append(node)
        x += w + self._word_spacing
        return x, y, line_idx

    def _newLine(self, x, y, line_idx):
        return self._left_margin, self._advanceY(y, line_idx), line_idx + 1

    def _renderTextChunk(self, chunk, x, y, line_idx):
        for word in chunk.split():
            x, y, line_idx = self._addWord(word, x, y, line_idx)
        return x, y, line_idx

    # Horizontal offset between consecutive levels of a stacked-satellite
    # stack. Each satellite shifts right by this amount relative to its
    # anchor, creating a staircase effect. The shifted layout leaves
    # exposed "shoulders" on each level — bottom-left of every primary/
    # mid-satellite, top-right of every satellite — where edge endpoints
    # attach so they are never occluded by the neighbouring level.
    _STACK_STAGGER = 10

    def _addStackedSatellite(self, anchor, eiid, text, line_idx):
        """Place a NodeItem just below `anchor` (flush vertically, shifted
        right by STACK_STAGGER) to represent an additional MAKEINSTANCE of
        the same EVENT. Same text as the primary so the stack reads as
        one event with N instances; the eiid is conveyed through the id
        badge (Show IDs) and the node_id, which is what the edge planner
        looks up.

        The satellite is appended to self._lines so that
        _resizeGutterIfNeeded shifts it together with the rest of its
        row when the gutter grows.

        Returns the new node so the caller can chain further satellites
        below it."""
        node = si.NodeItem(eiid, text=text)
        node.setFlag(QGraphicsItem.ItemIsMovable, False)
        anchor_bottom = anchor.pos().y() + anchor.rect().height() / 2
        node_h = node.rect().height()
        node.setPos(anchor.pos().x() + self._STACK_STAGGER,
                    anchor_bottom + node_h / 2)
        node._line_idx = line_idx
        # Flags consumed by LaneEdgeItem._biasX so the attach point lands
        # on the exposed shoulder rather than under the neighbour.
        node._has_stacked_above = True
        anchor._has_stacked_below = True
        # Push subsequent text rows down by this satellite's height so the
        # edge gutter stays below the whole stack rather than overlapping it.
        self._line_extra_height[line_idx] = (
            self._line_extra_height.get(line_idx, 0) + node_h)
        self.addItem(node)
        self._ensureLine(line_idx)
        self._lines[line_idx].append(node)
        return node

    def _layoutText(self, body, eid_to_node_ids):
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
                x, y, line_idx = self._newLine(x, y, line_idx)
                pos += 5
                continue

            if ch == '<':
                event_match = self._EVENT_RE.match(body, pos)
                if event_match:
                    eid_m = self._EID_RE.search(event_match.group(1))
                    inner = si.decodeText(self._stripInnerTags(event_match.group(2)).strip()) or "?"
                    if eid_m and eid_m.group(1) in eid_to_node_ids:
                        eiids = eid_to_node_ids[eid_m.group(1)]
                        x, y, line_idx = self._addNodeInline(eiids[0], inner, x, y, line_idx)
                        if len(eiids) > 1:
                            anchor = self.nodes[eiids[0]]
                            for extra_eiid in eiids[1:]:
                                anchor = self._addStackedSatellite(anchor, extra_eiid, inner, line_idx)
                    else:
                        x, y, line_idx = self._renderTextChunk(inner, x, y, line_idx)
                    pos = event_match.end()
                    continue

                timex_match = self._TIMEX_RE.match(body, pos)
                if timex_match:
                    tid_m = self._TID_RE.search(timex_match.group(1))
                    inner = si.decodeText(self._stripInnerTags(timex_match.group(2)).strip()) or "?"
                    placed = False
                    if tid_m:
                        tid = tid_m.group(1)
                        timex_node = self._graph.nodes.get(tid)
                        if timex_node is not None:
                            x, y, line_idx = self._addNodeInline(tid, inner, x, y, line_idx)
                            placed = True
                    if not placed:
                        x, y, line_idx = self._renderTextChunk(inner, x, y, line_idx)
                    pos = timex_match.end()
                    continue

                tag_match = self._ANY_TAG_RE.match(body, pos)
                if tag_match:
                    tag_compact = re.sub(r'\s+', '', tag_match.group(0).lower().strip())
                    if tag_compact in self._LINE_BREAK_TAGS:
                        x, y, line_idx = self._newLine(x, y, line_idx)
                    pos = tag_match.end()
                    continue

                x, y, line_idx = self._addWord('<', x, y, line_idx)
                pos += 1
                continue

            word_match = re.match(r'(?:(?!&#1[03];)[^\s<])+', body[pos:])
            if word_match:
                x, y, line_idx = self._addWord(word_match.group(0), x, y, line_idx)
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
        old_line_height = self._line_height
        self._gutter_height = needed_height
        new_line_height = self._line_height
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

    def _createScene(self):
        eid_to_node_ids = self._buildEventToNodeIdsMap()
        tml = getattr(self._graph, "time_ml_data", None) or ""
        body = self._extractTextBody(tml)
        self._layoutText(body, eid_to_node_ids)
        si.LaneEdgePlanner(self).drawEdges()
        self._prepareDocFunctionOverlay()

    def _docFunctionTitle(self, function):
        return self._DOC_FUNCTION_TITLES.get(function, function.replace("_", " ").title())

    def _prepareDocFunctionOverlay(self):
        """Builds the header boxes for every TIMEX3 with a functionInDocument
        other than NONE, stacked above the text, each in its function's colour."""
        self._doc_function_boxes = []
        timexes = [n for n in self._graph.nodes.values() if self._isDocumentFunctionTimex3(n)]
        if not timexes:
            return
        # Stable order: creation time first, then by tid.
        timexes.sort(key=lambda n: (0 if self._isCreationTimeTimex3(n) else 1,
                                     getattr(n, "tID", 0)))
        fm = QFontMetrics(self._font)
        h = fm.height() + 2 * self._DCT_PADDING
        gap = 4
        # The lowest box sits just above the text; the rest stack upward.
        base_top = self._top_margin - self._gutter_height - h - 5
        n = len(timexes)
        boxes = []
        for i, tx in enumerate(timexes):
            function = tx.documentFunction.upper()
            value = getattr(tx, "value", None) or "?"
            phrase = getattr(tx, "phrase", None)
            label = f"{self._docFunctionTitle(function)}: {value}"
            if phrase and phrase != value:
                label += f" ({phrase})"
            text_rect = fm.boundingRect(label)
            w = text_rect.width() + 2 * self._DCT_PADDING
            y = base_top - (n - 1 - i) * (h + gap)
            rect = QRectF(self._left_margin, y, w, h)
            color = self._DOC_FUNCTION_COLORS.get(function, self._DOC_FUNCTION_DEFAULT_COLOR)
            boxes.append((rect, label, text_rect, color))
        self._doc_function_boxes = boxes
        # Drawn via drawForeground (not scene items), so extend sceneRect to
        # keep the boxes reachable when scrolling.
        united = self.itemsBoundingRect()
        for rect, *_ in boxes:
            united = united.united(rect)
        self.setSceneRect(united.adjusted(-10, -10, 10, 10))

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self._doc_function_boxes:
            return
        painter.save()
        painter.setFont(self._font)
        for box_rect, label, text_rect, color in self._doc_function_boxes:
            if not rect.intersects(box_rect):
                continue
            painter.setBrush(QBrush(self._DCT_BG))
            painter.setPen(QPen(color, 1))
            painter.drawRect(box_rect)
            painter.setPen(color)
            painter.drawText(box_rect.x() + self._DCT_PADDING - text_rect.left(),
                             box_rect.y() + self._DCT_PADDING - text_rect.top(),
                             label)
        painter.restore()
