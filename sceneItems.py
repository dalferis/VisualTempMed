import html
import math
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem, QStyle
)
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath, QPainterPathStroker, QFont
from PySide6.QtCore import Qt, QPointF, QLineF


def decodeText(s):
    if not s:
        return s
    return html.unescape(s)


# Edge colour for date-inferred ordering links (dash-dot pen), distinct from
# annotated TLINK (black) / SLINK (red) / ALINK (blue) and from the dashed
# Connectivity_Increaser suggestions.
DATE_INFERRED_COLOR = QColor(150, 0, 150)   # purple


def linkColor(link, date_inferred=False):
    if date_inferred:
        return DATE_INFERRED_COLOR
    if link.link_tag == "SLINK":
        return Qt.red
    if link.link_tag == "ALINK":
        return Qt.blue
    return Qt.black


class NodeItem(QGraphicsRectItem):
    EVENT_BRUSH = QBrush(Qt.lightGray)
    TIMEX_BRUSH = QBrush(QColor(200, 230, 201))  # soft green

    def __init__(self, node_id, text=""):
        self.node_id = node_id
        self.edges = []

        self.label = QGraphicsTextItem(text)
        self.label.setDefaultTextColor(Qt.blue)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label.setFont(font)

        text_rect = self.label.boundingRect()
        padding = -2
        width = text_rect.width() + padding
        height = text_rect.height() + padding

        super().__init__(-width/2, -height/2, width, height)

        is_timex = isinstance(node_id, str) and len(node_id) > 1 and node_id[0] == 't' and node_id[1:].isdigit()
        self.setBrush(self.TIMEX_BRUSH if is_timex else self.EVENT_BRUSH)
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(15)

        self.label.setParentItem(self)
        self.label.setPos(-text_rect.width()/2, -text_rect.height()/2)

        self.createIdBadge()

    def createIdBadge(self):
        padding = -2

        self.id_text = QGraphicsTextItem(str(self.node_id), self)
        self.id_text.setDefaultTextColor(Qt.white)

        font = QFont()
        font.setPointSize(6)
        font.setBold(True)
        self.id_text.setFont(font)

        text_rect = self.id_text.boundingRect()

        badge_width = text_rect.width() + padding * 2
        badge_height = text_rect.height() + padding * 2

        self.id_bg = QGraphicsRectItem(self)
        self.id_bg.setBrush(QBrush(Qt.darkGray))
        self.id_bg.setPen(QPen(Qt.black, 1))

        node_rect = self.rect()

        x = node_rect.left() - 4
        y = node_rect.top() - 10

        self.id_bg.setRect(x, y, badge_width, badge_height)

        self.id_text.setPos(x + padding, y + padding)

        self.id_bg.setZValue(2)
        self.id_text.setZValue(3)

    def addEdge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.updatePosition()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        # Replace Qt's default selection rendering (1-px dashed) with a
        # thicker dashed border so the selected node stands out.
        selected = bool(option.state & QStyle.State_Selected)
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)
        if selected:
            painter.save()
            painter.setPen(QPen(Qt.black, 3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())
            painter.restore()


class EdgeItem(QGraphicsPathItem):
    _hit_width = 8

    def __init__(self, source, target, text="", text_color=Qt.black, link_color=Qt.black, curvature=0.0):
        super().__init__()

        self.source = source
        self.target = target
        self.curvature = curvature

        self.setPen(QPen(link_color, 2))
        self.setZValue(-1)

        source.addEdge(self)
        target.addEdge(self)

        self.label = QGraphicsTextItem(text, self)
        self.label.setDefaultTextColor(text_color)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(self._hit_width)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.updatePosition()
        return super().itemChange(change, value)

    def intersectLineWithRect(self, center_from, center_to, rect, item_pos):
        line = QLineF(center_from, center_to)
        r = rect.translated(item_pos)

        edges = [
            QLineF(r.topLeft(), r.topRight()),
            QLineF(r.topRight(), r.bottomRight()),
            QLineF(r.bottomRight(), r.bottomLeft()),
            QLineF(r.bottomLeft(), r.topLeft())
        ]

        for edge in edges:
            intersection_type, point = line.intersects(edge)
            if intersection_type == QLineF.BoundedIntersection:
                return point

        return center_from

    def hasObstacleBetween(self, start, end):
        scene = self.scene()
        if not scene:
            return False

        line = QLineF(start, end)

        for item in scene.items():

            if not isinstance(item, NodeItem):
                continue

            if item is self.source or item is self.target:
                continue

            rect = item.rect().translated(item.pos())

            edges = [
                QLineF(rect.topLeft(), rect.topRight()),
                QLineF(rect.topRight(), rect.bottomRight()),
                QLineF(rect.bottomRight(), rect.bottomLeft()),
                QLineF(rect.bottomLeft(), rect.topLeft())
            ]

            for edge in edges:
                intersection_type, _ = line.intersects(edge)
                if intersection_type == QLineF.BoundedIntersection:
                    return True

        return False

    def updatePosition(self):
        rect1 = self.source.rect()
        rect2 = self.target.rect()

        center1 = self.source.pos() + rect1.center()
        center2 = self.target.pos() + rect2.center()

        start = self.intersectLineWithRect(
            center1, center2, rect1, self.source.pos()
        )

        end = self.intersectLineWithRect(
            center2, center1, rect2, self.target.pos()
        )

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        base_angle = math.atan2(dy, dx)

        path = QPainterPath()
        path.moveTo(start)

        ctrl = None
        if self.curvature != 0:
            curvature = self.curvature
        elif self.hasObstacleBetween(start, end):
            curvature = 0.25
        else:
            curvature = 0.0

        if curvature != 0:
            ctrl = QPointF(
                (start.x() + end.x()) / 2 - dy * curvature,
                (start.y() + end.y()) / 2 + dx * curvature
            )
            path.quadTo(ctrl, end)
            tx = end.x() - ctrl.x()
            ty = end.y() - ctrl.y()
            angle = math.atan2(ty, tx)
        else:
            path.lineTo(end)
            angle = base_angle

        # Arrow
        arrow_size = 12
        arrow_p1 = end - QPointF(
            arrow_size * math.cos(angle - math.pi / 6),
            arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = end - QPointF(
            arrow_size * math.cos(angle + math.pi / 6),
            arrow_size * math.sin(angle + math.pi / 6)
        )

        path.moveTo(end)
        path.lineTo(arrow_p1)
        path.moveTo(end)
        path.lineTo(arrow_p2)
        self.setPath(path)

        # Label
        if curvature != 0 and ctrl is not None:
            t = 0.5

            # Real point on the curve (quadratic Bézier)
            x = (1 - t)**2 * start.x() + 2 * (1 - t) * t * ctrl.x() + t**2 * end.x()
            y = (1 - t)**2 * start.y() + 2 * (1 - t) * t * ctrl.y() + t**2 * end.y()

            label_pos = QPointF(x, y)

            # Real tangent of the curve
            tx = 2*(1 - t)*(ctrl.x() - start.x()) + 2*t*(end.x() - ctrl.x())
            ty = 2*(1 - t)*(ctrl.y() - start.y()) + 2*t*(end.y() - ctrl.y())

            length = math.hypot(tx, ty)

            if length != 0:
                nx = -ty / length
                ny = tx / length

                offset = 15
                label_pos += QPointF(nx * offset, ny * offset)

        else:
            # Beeline - offset the label perpendicular to the segment so it
            # doesn't overlap the edge line itself.
            label_pos = QPointF(
                (start.x() + end.x()) / 2,
                (start.y() + end.y()) / 2
            )
            length = math.hypot(dx, dy)
            if length != 0:
                nx = -dy / length
                ny = dx / length
                # Prefer placing the label above the edge in screen coords.
                if ny > 0:
                    nx, ny = -nx, -ny
                offset = 15
                label_pos += QPointF(nx * offset, ny * offset)

        # Center text
        rect = self.label.boundingRect()
        label_pos -= QPointF(rect.width() / 2, rect.height() / 2)

        self.label.setPos(label_pos)


class LaneEdgeItem(EdgeItem):
    """Edge with orthogonal routing through inter-line gutters and a left rail.

    Path geometry is described by a ``plan`` dict produced by a LaneEdgePlanner:
      mode: 'same_line' | 'adjacent' | 'cross_line'
      same_line: gutter, main_track
      adjacent:  gutter, main_track (with src_line/tgt_line for direction)
      cross_line: src_gutter, src_track, tgt_gutter, tgt_track, rail_track
    The scene must expose ``gutterY(idx, track)`` and ``railX(track)`` methods.
    """

    _arrow_size = 10
    _normal_width = 2
    _highlight_width = 4
    _normal_z = 5
    # Must exceed NodeItem.setZValue (currently 15). The label and label_bg
    # are children of the edge and therefore stack with the edge in the
    # scene's global Z order, no matter what their own Z is. With a value
    # below NodeItem's Z the highlighted label only jumps above other
    # labels, but stays hidden under any node it overlaps -- which in
    # textView is unfixable from the user side, because nodes are not
    # movable there.
    _highlight_z = 20
    _label_margin = 3

    def __init__(self, source, target, scene_ref, plan, text="", text_color=Qt.black, link_color=Qt.black):
        self._scene_ref = scene_ref
        self._plan = plan
        self._link_color = link_color
        self._suggested = bool(plan.get('suggested', False))
        self._date_inferred = bool(plan.get('date_inferred', False))
        self.link = plan.get('link')
        self._highlighted = False
        super().__init__(source, target, text=text, text_color=text_color, link_color=link_color, curvature=0.0)
        self.setZValue(self._normal_z)
        self._applyPen()
        self._label_bg = QGraphicsRectItem(self)
        self._label_bg.setBrush(QBrush(QColor(255, 255, 255, 220)))
        self._label_bg.setPen(QPen(Qt.NoPen))
        self._label_bg.setZValue(-0.5)
        self.label.setZValue(0)
        if self._suggested:
            italic = self.label.font()
            italic.setItalic(True)
            self.label.setFont(italic)

    def _applyPen(self):
        width = self._highlight_width if self._highlighted else self._normal_width
        pen = QPen(self._link_color, width)
        if self._suggested:
            pen.setStyle(Qt.DashLine)
        elif self._date_inferred:
            pen.setStyle(Qt.DashDotLine)
        self.setPen(pen)

    def setHighlighted(self, on):
        if self._highlighted == on:
            return
        self._highlighted = on
        self._applyPen()
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

    @staticmethod
    def _attachY(rect, lane_y):
        """Returns (y, side) for the side of ``rect`` (top/bottom) closest to ``lane_y``.

        Recomputed each call so that endpoints stay on the correct side of the
        node when it is dragged across the gutter.
        """
        top = rect.top()
        bottom = rect.bottom()
        if lane_y <= top:
            return top, 'top'
        if lane_y >= bottom:
            return bottom, 'bottom'
        # Gutter falls inside the node rect — pick the nearer edge.
        return (top, 'top') if (lane_y - top) < (bottom - lane_y) else (bottom, 'bottom')

    @staticmethod
    def _biasX(node, rect, default_x, side):
        """For nodes participating in a stacked-satellite stack, shift the
        attach x toward the exposed shoulder so the endpoint is not
        occluded by the neighbouring level. The stack staggers each
        satellite to the right; the exposed strip is on the LEFT of the
        bottom side and on the RIGHT of the top side."""
        BIAS = 5
        if side == 'bottom' and getattr(node, '_has_stacked_below', False):
            return rect.left() + BIAS
        if side == 'top' and getattr(node, '_has_stacked_above', False):
            return rect.right() - BIAS
        return default_x

    def updatePosition(self):
        scene = self._scene_ref
        plan = self._plan

        src_rect = self.source.rect().translated(self.source.pos())
        tgt_rect = self.target.rect().translated(self.target.pos())
        # Attach as a fraction of the node's width so the endpoint follows the
        # node when it is dragged horizontally. Fall back to the center.
        src_frac = plan.get('src_attach_fraction', 0.5)
        tgt_frac = plan.get('tgt_attach_fraction', 0.5)
        src_x = src_rect.left() + src_frac * src_rect.width()
        tgt_x = tgt_rect.left() + tgt_frac * tgt_rect.width()

        path = QPainterPath()

        if plan['mode'] in ('same_line', 'adjacent'):
            lane_y = scene.gutterY(plan['gutter'], plan.get('main_track', 0))
            src_y, src_side = self._attachY(src_rect, lane_y)
            tgt_y, tgt_side = self._attachY(tgt_rect, lane_y)
            src_x = self._biasX(self.source, src_rect, src_x, src_side)
            tgt_x = self._biasX(self.target, tgt_rect, tgt_x, tgt_side)

            path.moveTo(src_x, src_y)
            path.lineTo(src_x, lane_y)
            path.lineTo(tgt_x, lane_y)
            path.lineTo(tgt_x, tgt_y)

            end_x, end_y = tgt_x, tgt_y
            arrow_angle = math.pi / 2 if tgt_side == 'top' else -math.pi / 2
            label_pos = QPointF((src_x + tgt_x) / 2, lane_y - 8)
        else:
            src_lane_y = scene.gutterY(plan['src_gutter'], plan.get('src_track', 0))
            tgt_lane_y = scene.gutterY(plan['tgt_gutter'], plan.get('tgt_track', 0))
            rail_x = scene.railX(plan.get('rail_track', 0))
            src_y, src_side = self._attachY(src_rect, src_lane_y)
            tgt_y, tgt_side = self._attachY(tgt_rect, tgt_lane_y)
            src_x = self._biasX(self.source, src_rect, src_x, src_side)
            tgt_x = self._biasX(self.target, tgt_rect, tgt_x, tgt_side)

            path.moveTo(src_x, src_y)
            path.lineTo(src_x, src_lane_y)
            path.lineTo(rail_x, src_lane_y)
            path.lineTo(rail_x, tgt_lane_y)
            path.lineTo(tgt_x, tgt_lane_y)
            path.lineTo(tgt_x, tgt_y)

            end_x, end_y = tgt_x, tgt_y
            arrow_angle = math.pi / 2 if tgt_side == 'top' else -math.pi / 2
            label_pos = QPointF(rail_x + 6, (src_lane_y + tgt_lane_y) / 2)

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


class LaneEdgePlanner:
    """Builds orthogonal edge plans and instantiates LaneEdgeItems on a scene.

    The scene is expected to expose:
      - ``_graph``                                   (pytlex Graph object)
      - ``_tlex``                                    (pytlex TLEX object)
      - ``nodes``                                    ({node_id: NodeItem})
      - ``_rail_x``                                  (float; x of the right rail)
      - ``lineOfNode(node_item) -> int``             (logical row index)
      - ``isCreationTimeLink(link) -> bool``         (filter for DCT links)
      - ``gutterY(idx, track) -> float``             (used by LaneEdgeItem)
      - ``railX(track) -> float``                    (used by LaneEdgeItem)
      - optional: ``_resizeGutterIfNeeded(max_tracks_per_gutter)``  (re-layout
        the scene to accommodate dense gutters; called only if defined).
    """

    def __init__(self, scene, track_spacing=5, gutter_padding=5):
        self.scene = scene
        self.track_spacing = track_spacing
        self.gutter_padding = gutter_padding

    def drawEdges(self):
        plans = self._buildEdgePlans()
        if not plans:
            return
        self._distributeAttachments(plans)
        self._refreshIntervals(plans)
        max_tracks_per_gutter, _ = self._allocateTracks(plans)
        resize = getattr(self.scene, '_resizeGutterIfNeeded', None)
        if callable(resize):
            resize(max_tracks_per_gutter)
        for plan in plans:
            edge = LaneEdgeItem(
                plan['source'], plan['target'],
                scene_ref=self.scene, plan=plan,
                text=plan['text'],
                text_color=plan['text_color'],
                link_color=plan['link_color'],
            )
            self.scene.addItem(edge)

    def _buildEdgePlans(self):
        s = self.scene
        # NOTE: graph.links is restored after partitioning by TLEX, so it
        # already contains every TLINK / SLINK / ALINK. Earlier the planner
        # also merged in tlex.s_links, but that produced visible duplicates
        # for every SLINK (drawn twice, perfectly overlapping). Keep
        # graph.links as the single source of truth for annotated links.
        annotated = [v for v in s._graph.links.values() if not s.isCreationTimeLink(v)]
        # Suggested links from Connectivity_Increaser anchor each disconnected
        # subgraph to the DCT, so by construction every endpoint touches the
        # DCT. We deliberately keep them past the isCreationTimeLink filter.
        suggested = getattr(s._tlex, 'suggested_links', None) or []
        candidate_links = [(v, False) for v in annotated] + [(v, True) for v in suggested]

        plans = []
        for link, is_suggested in candidate_links:
            src = s.nodes.get(link.start_node)
            tgt = s.nodes.get(link.related_to_node)
            if src is None or tgt is None:
                continue
            date_inferred = getattr(link, '_date_inferred', False)
            src_line = s.lineOfNode(src)
            tgt_line = s.lineOfNode(tgt)
            src_cx = src.pos().x()
            tgt_cx = tgt.pos().x()
            plan = {
                'source': src, 'target': tgt,
                'text': link.rel_type,
                'text_color': QColor(145, 145, 0),
                'link_color': linkColor(link, date_inferred),
                'src_line': src_line, 'tgt_line': tgt_line,
                'src_cx': src_cx, 'tgt_cx': tgt_cx,
                'suggested': is_suggested,
                'date_inferred': date_inferred,
                'link': link,
            }
            if src_line == tgt_line:
                plan['mode'] = 'same_line'
                plan['gutter'] = src_line
                plan['x_min'] = min(src_cx, tgt_cx)
                plan['x_max'] = max(src_cx, tgt_cx)
            elif abs(src_line - tgt_line) == 1:
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
                plan['src_x_min'] = min(src_cx, s._rail_x)
                plan['src_x_max'] = max(src_cx, s._rail_x)
                plan['tgt_x_min'] = min(tgt_cx, s._rail_x)
                plan['tgt_x_max'] = max(tgt_cx, s._rail_x)
            plans.append(plan)
        return plans

    @staticmethod
    def _greedyAssignTracks(intervals, get_start, get_end, set_track):
        """Greedy interval-graph coloring; assigns smallest non-conflicting track to each interval."""
        ordered = sorted(intervals, key=get_start)
        track_ends = []
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
        gutter_intervals = {}
        rail_intervals = []

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
            self._greedyAssignTracks(intervals,
                                     get_start=lambda it: it[0],
                                     get_end=lambda it: it[1],
                                     set_track=set_gutter_track)
            max_tracks_per_gutter[gutter] = max(
                (1 + (it[2]['main_track'] if it[3] == 'main'
                      else it[2]['src_track'] if it[3] == 'src'
                      else it[2]['tgt_track']) for it in intervals),
                default=0,
            )

        def set_rail_track(item, track):
            item[2]['rail_track'] = track

        self._greedyAssignTracks(rail_intervals,
                                 get_start=lambda it: it[0],
                                 get_end=lambda it: it[1],
                                 set_track=set_rail_track)
        max_rail_tracks = max((p.get('rail_track', 0) + 1 for p in plans if p['mode'] == 'cross_line'), default=0)
        return max_tracks_per_gutter, max_rail_tracks

    @staticmethod
    def _sidesFor(plan):
        """Returns (src_side, tgt_side), each 'top' or 'bottom'."""
        if plan['mode'] == 'same_line':
            return 'top', 'top'
        if plan['src_line'] < plan['tgt_line']:
            return 'bottom', 'top'
        return 'top', 'bottom'

    def _distributeAttachments(self, plans):
        """Spread edge endpoints along each node's top/bottom edge to avoid overlap."""
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
                        fraction = 0.5
                    else:
                        fraction = (i + 1) / (n + 1)
                    x = left + fraction * width
                    if role == 'src':
                        plan['src_attach_x'] = x          # scene x at layout time (used by track allocation)
                        plan['src_attach_fraction'] = fraction  # used at render time so the endpoint follows the node
                    else:
                        plan['tgt_attach_x'] = x
                        plan['tgt_attach_fraction'] = fraction

    def _refreshIntervals(self, plans):
        rail_x = self.scene._rail_x
        for plan in plans:
            sx = plan.get('src_attach_x', plan['src_cx'])
            tx = plan.get('tgt_attach_x', plan['tgt_cx'])
            if plan['mode'] in ('same_line', 'adjacent'):
                plan['x_min'] = min(sx, tx)
                plan['x_max'] = max(sx, tx)
            else:
                plan['src_x_min'] = min(sx, rail_x)
                plan['src_x_max'] = max(sx, rail_x)
                plan['tgt_x_min'] = min(tx, rail_x)
                plan['tgt_x_max'] = max(tx, rail_x)
