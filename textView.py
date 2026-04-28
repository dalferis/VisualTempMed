import math
import re
import sceneItems as si
from pytlex_core.data import Instance, TimeX
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem, QGraphicsRectItem
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QBrush
from PySide6.QtCore import Qt, QPointF


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


class LaneEdgeItem(si.EdgeItem):
    """Edge with orthogonal routing through inter-line gutters and a left rail.

    Path geometry is described by a ``plan`` dict produced by TextScene:
      mode: 'same_line' | 'cross_line'
      same_line: gutter, main_track
      cross_line: src_gutter, src_track, tgt_gutter, tgt_track, rail_track
    """

    _arrow_size = 10
    _normal_width = 2
    _highlight_width = 4
    _normal_z = 5
    _highlight_z = 10
    _label_margin = 3

    def __init__(self, source, target, scene_ref, plan,
                 text="", text_color=Qt.black, link_color=Qt.black):
        self._scene_ref = scene_ref
        self._plan = plan
        self._link_color = link_color
        self._highlighted = False
        super().__init__(source, target, text=text,
                         text_color=text_color, link_color=link_color, curvature=0.0)
        # Lift the whole edge above text and nodes (default zValue 0).
        self.setZValue(self._normal_z)
        # Translucent backplate behind the label, kept inside the edge so it
        # follows the same z layer.
        self._label_bg = QGraphicsRectItem(self)
        self._label_bg.setBrush(QBrush(QColor(255, 255, 255, 220)))
        self._label_bg.setPen(QPen(Qt.NoPen))
        self._label_bg.setZValue(-0.5)  # below label (default 0), above edge path
        self.label.setZValue(0)

    def setHighlighted(self, on):
        if self._highlighted == on:
            return
        self._highlighted = on
        pen = QPen(self._link_color, self._highlight_width if on else self._normal_width)
        self.setPen(pen)
        self.setZValue(self._highlight_z if on else self._normal_z)
        font = self.label.font()
        font.setBold(on)
        self.label.setFont(font)

    def _drawArrow(self, path, end_x, end_y, angle):
        s = self._arrow_size
        p1 = QPointF(
            end_x - s * math.cos(angle - math.pi / 6),
            end_y - s * math.sin(angle - math.pi / 6)
        )
        p2 = QPointF(
            end_x - s * math.cos(angle + math.pi / 6),
            end_y - s * math.sin(angle + math.pi / 6)
        )
        path.moveTo(end_x, end_y)
        path.lineTo(p1)
        path.moveTo(end_x, end_y)
        path.lineTo(p2)

    def updatePosition(self):
        scene = self._scene_ref
        plan = self._plan

        src_rect = self.source.rect().translated(self.source.pos())
        tgt_rect = self.target.rect().translated(self.target.pos())
        src_x = plan.get('src_attach_x', src_rect.center().x())
        tgt_x = plan.get('tgt_attach_x', tgt_rect.center().x())
        src_top = src_rect.top()
        src_bottom = src_rect.bottom()
        tgt_top = tgt_rect.top()
        tgt_bottom = tgt_rect.bottom()

        path = QPainterPath()

        if plan['mode'] == 'same_line':
            lane_y = scene.gutterY(plan['gutter'], plan.get('main_track', 0))
            path.moveTo(src_x, src_top)
            path.lineTo(src_x, lane_y)
            path.lineTo(tgt_x, lane_y)
            path.lineTo(tgt_x, tgt_top)
            end_x, end_y = tgt_x, tgt_top
            arrow_angle = math.pi / 2
            label_pos = QPointF((src_x + tgt_x) / 2, lane_y - 8)
        elif plan['mode'] == 'adjacent':
            lane_y = scene.gutterY(plan['gutter'], plan.get('main_track', 0))
            if plan['src_line'] < plan['tgt_line']:
                path.moveTo(src_x, src_bottom)
                path.lineTo(src_x, lane_y)
                path.lineTo(tgt_x, lane_y)
                path.lineTo(tgt_x, tgt_top)
                end_x, end_y = tgt_x, tgt_top
                arrow_angle = math.pi / 2
            else:
                path.moveTo(src_x, src_top)
                path.lineTo(src_x, lane_y)
                path.lineTo(tgt_x, lane_y)
                path.lineTo(tgt_x, tgt_bottom)
                end_x, end_y = tgt_x, tgt_bottom
                arrow_angle = -math.pi / 2
            label_pos = QPointF((src_x + tgt_x) / 2, lane_y - 8)
        else:
            src_lane_y = scene.gutterY(plan['src_gutter'], plan.get('src_track', 0))
            tgt_lane_y = scene.gutterY(plan['tgt_gutter'], plan.get('tgt_track', 0))
            rail_x = scene.railX(plan.get('rail_track', 0))

            if plan['src_line'] < plan['tgt_line']:
                path.moveTo(src_x, src_bottom)
                path.lineTo(src_x, src_lane_y)
                path.lineTo(rail_x, src_lane_y)
                path.lineTo(rail_x, tgt_lane_y)
                path.lineTo(tgt_x, tgt_lane_y)
                path.lineTo(tgt_x, tgt_top)
                end_x, end_y = tgt_x, tgt_top
                arrow_angle = math.pi / 2
            else:
                path.moveTo(src_x, src_top)
                path.lineTo(src_x, src_lane_y)
                path.lineTo(rail_x, src_lane_y)
                path.lineTo(rail_x, tgt_lane_y)
                path.lineTo(tgt_x, tgt_lane_y)
                path.lineTo(tgt_x, tgt_bottom)
                end_x, end_y = tgt_x, tgt_bottom
                arrow_angle = -math.pi / 2
            label_pos = QPointF(rail_x - 6, (src_lane_y + tgt_lane_y) / 2)

        self._drawArrow(path, end_x, end_y, arrow_angle)
        self.setPath(path)

        rect = self.label.boundingRect()
        lx = label_pos.x() - rect.width() / 2
        ly = label_pos.y() - rect.height() / 2
        self.label.setPos(lx, ly)
        if getattr(self, '_label_bg', None) is not None:
            m = self._label_margin
            self._label_bg.setRect(lx - m, ly - m,
                                    rect.width() + 2 * m, rect.height() + 2 * m)


class TextScene(QGraphicsScene):
    _max_line_width = 1200
    _text_height = 26
    _gutter_height = 28
    _word_spacing = 5
    _left_margin = 10
    _top_margin = 30
    _left_rail_x = -60

    _track_spacing = 5
    _gutter_padding = 5

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
        elif isinstance(clicked, si.NodeItem):
            outgoing = [e for e in self.items()
                        if isinstance(e, LaneEdgeItem) and e.source is clicked]
            for e in outgoing:
                e.setHighlighted(True)
            self._highlighted_edges = outgoing

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
        return self._left_rail_x - (track + 0.5) * self._track_spacing

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

    # ------- Edge planning and track allocation -------

    def _buildEdgePlans(self):
        candidate_links = [v for v in self._graph.links.values() if not self.isCreationTimeLink(v)]
        candidate_links += [v for v in self._tlex.s_links if not self.isCreationTimeLink(v)]

        plans = []
        for link in candidate_links:
            src = self.nodes.get(link.start_node)
            tgt = self.nodes.get(link.related_to_node)
            if src is None or tgt is None:
                continue
            color = Qt.black if link.link_tag == "TLINK" else Qt.red if link.link_tag == "SLINK" else Qt.blue
            src_line = self.lineOfNode(src)
            tgt_line = self.lineOfNode(tgt)
            src_cx = src.pos().x()
            tgt_cx = tgt.pos().x()
            plan = {
                'source': src, 'target': tgt,
                'text': link.rel_type,
                'text_color': QColor(color).darker(150),
                'link_color': color,
                'src_line': src_line, 'tgt_line': tgt_line,
                'src_cx': src_cx, 'tgt_cx': tgt_cx,
            }
            if src_line == tgt_line:
                plan['mode'] = 'same_line'
                plan['gutter'] = src_line  # gutter above this line
                plan['x_min'] = min(src_cx, tgt_cx)
                plan['x_max'] = max(src_cx, tgt_cx)
            elif abs(src_line - tgt_line) == 1:
                # Vertically adjacent: take the shortest path through the single
                # gutter between the two lines (no rail detour).
                plan['mode'] = 'adjacent'
                plan['gutter'] = max(src_line, tgt_line)
                plan['x_min'] = min(src_cx, tgt_cx)
                plan['x_max'] = max(src_cx, tgt_cx)
            else:
                plan['mode'] = 'cross_line'
                if src_line < tgt_line:
                    plan['src_gutter'] = src_line + 1
                    plan['tgt_gutter'] = tgt_line
                else:
                    plan['src_gutter'] = src_line
                    plan['tgt_gutter'] = tgt_line + 1
                plan['src_x_min'] = min(src_cx, self._left_rail_x)
                plan['src_x_max'] = max(src_cx, self._left_rail_x)
                plan['tgt_x_min'] = min(tgt_cx, self._left_rail_x)
                plan['tgt_x_max'] = max(tgt_cx, self._left_rail_x)
            plans.append(plan)
        return plans

    @staticmethod
    def _greedyAssignTracks(intervals, get_start, get_end, set_track):
        """Greedy interval-graph coloring; assigns smallest non-conflicting track to each interval."""
        ordered = sorted(intervals, key=get_start)
        track_ends = []  # latest end per track
        for item in ordered:
            start = get_start(item)
            end = get_end(item)
            assigned = None
            for t, prev_end in enumerate(track_ends):
                if prev_end < start:
                    track_ends[t] = end
                    assigned = t
                    break
            if assigned is None:
                track_ends.append(end)
                assigned = len(track_ends) - 1
            set_track(item, assigned)

    def _allocateTracks(self, plans):
        gutter_intervals = {}  # gutter_idx -> list of (x_min, x_max, plan, key)
        rail_intervals = []    # list of (g_min, g_max, plan)

        for plan in plans:
            if plan['mode'] in ('same_line', 'adjacent'):
                gutter_intervals.setdefault(plan['gutter'], []).append(
                    [plan['x_min'], plan['x_max'], plan, 'main']
                )
            else:
                gutter_intervals.setdefault(plan['src_gutter'], []).append(
                    [plan['src_x_min'], plan['src_x_max'], plan, 'src']
                )
                gutter_intervals.setdefault(plan['tgt_gutter'], []).append(
                    [plan['tgt_x_min'], plan['tgt_x_max'], plan, 'tgt']
                )
                g_min = min(plan['src_gutter'], plan['tgt_gutter'])
                g_max = max(plan['src_gutter'], plan['tgt_gutter'])
                rail_intervals.append([g_min, g_max, plan])

        def set_gutter_track(item, track):
            _, _, plan, key = item
            if key == 'main':
                plan['main_track'] = track
            elif key == 'src':
                plan['src_track'] = track
            else:
                plan['tgt_track'] = track

        max_tracks_per_gutter = {}
        for gutter, intervals in gutter_intervals.items():
            self._greedyAssignTracks(
                intervals,
                get_start=lambda it: it[0],
                get_end=lambda it: it[1],
                set_track=set_gutter_track,
            )
            max_tracks_per_gutter[gutter] = max(
                (1 + (it[2]['main_track'] if it[3] == 'main'
                      else it[2]['src_track'] if it[3] == 'src'
                      else it[2]['tgt_track']) for it in intervals),
                default=0,
            )

        def set_rail_track(item, track):
            item[2]['rail_track'] = track

        self._greedyAssignTracks(
            rail_intervals,
            get_start=lambda it: it[0],
            get_end=lambda it: it[1],
            set_track=set_rail_track,
        )
        max_rail_tracks = max((p.get('rail_track', 0) + 1 for p in plans if p['mode'] == 'cross_line'), default=0)

        return max_tracks_per_gutter, max_rail_tracks

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

    # ------- Orchestration -------

    def drawEdges(self):
        plans = self._buildEdgePlans()
        if not plans:
            return
        self._distributeAttachments(plans)
        self._refreshIntervals(plans)
        max_tracks_per_gutter, _ = self._allocateTracks(plans)
        self._resizeGutterIfNeeded(max_tracks_per_gutter)
        for plan in plans:
            edge = LaneEdgeItem(
                plan['source'], plan['target'],
                scene_ref=self, plan=plan,
                text=plan['text'],
                text_color=plan['text_color'],
                link_color=plan['link_color'],
            )
            self.addItem(edge)

    @staticmethod
    def _sidesFor(plan):
        """Return (src_side, tgt_side), each 'top' or 'bottom'."""
        if plan['mode'] == 'same_line':
            return 'top', 'top'
        if plan['src_line'] < plan['tgt_line']:
            return 'bottom', 'top'
        return 'top', 'bottom'

    def _distributeAttachments(self, plans):
        """Spread edge endpoints along each node's top/bottom edge to avoid overlaps.

        Sort edges sharing a node-side by the x of the other endpoint, then place
        them at evenly-spaced x positions across the node's width.
        """
        attachments = {}
        for plan in plans:
            src_side, tgt_side = self._sidesFor(plan)
            src = plan['source']
            tgt = plan['target']
            attachments.setdefault(id(src), {'node': src, 'top': [], 'bottom': []})
            attachments.setdefault(id(tgt), {'node': tgt, 'top': [], 'bottom': []})
            attachments[id(src)][src_side].append((plan, 'src', plan['tgt_cx']))
            attachments[id(tgt)][tgt_side].append((plan, 'tgt', plan['src_cx']))

        for entry in attachments.values():
            node = entry['node']
            rect = node.rect().translated(node.pos())
            left, right = rect.left(), rect.right()
            width = right - left
            for side in ('top', 'bottom'):
                items = entry[side]
                n = len(items)
                if n == 0:
                    continue
                items.sort(key=lambda it: it[2])
                for i, (plan, role, _) in enumerate(items):
                    if n == 1:
                        x = (left + right) / 2
                    else:
                        x = left + (i + 1) * width / (n + 1)
                    if role == 'src':
                        plan['src_attach_x'] = x
                    else:
                        plan['tgt_attach_x'] = x

    def _refreshIntervals(self, plans):
        """Recompute horizontal intervals using the distributed attachment x's."""
        for plan in plans:
            sx = plan.get('src_attach_x', plan['src_cx'])
            tx = plan.get('tgt_attach_x', plan['tgt_cx'])
            if plan['mode'] in ('same_line', 'adjacent'):
                plan['x_min'] = min(sx, tx)
                plan['x_max'] = max(sx, tx)
            else:
                plan['src_x_min'] = min(sx, self._left_rail_x)
                plan['src_x_max'] = max(sx, self._left_rail_x)
                plan['tgt_x_min'] = min(tx, self._left_rail_x)
                plan['tgt_x_max'] = max(tx, self._left_rail_x)

    def createScene(self):
        eid_to_node_id = self.buildEventToNodeIdMap()
        tml = getattr(self._graph, "time_ml_data", None) or ""
        body = self.extractTextBody(tml)
        self.layoutText(body, eid_to_node_id)
        self.drawEdges()
