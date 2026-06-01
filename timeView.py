import math
from collections import defaultdict
import networkx as nx
import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from pytlex_core.timeline.Timeline import find_timeline
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QRectF, Signal


class TimeView(QGraphicsView):
    def __init__(self, model):
        self.scene = TimeScene(model)
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

class TimeScene(QGraphicsScene):
    nodeClicked = Signal(str)
    edgeClicked = Signal(object)
    selectionCleared = Signal()

    _graph: Graph.Graph
    _tlex: TLEX.TLEX

    _max_columns = 15
    _horizontal_distance = 210
    _vertical_distance = 110
    _x_origin = 130  # fixed x of the first column, shared by all partitions
    _partition_gap = 40  # extra vertical space between successive partitions
    _partition_label_margin = 12  # horizontal gap between partition header and first node
    _track_spacing = 5
    _gutter_padding = 5
    _top_gutter_height = 40  # reserved space above the first row for edges
    _rail_margin = 30  # horizontal gap between rightmost content and the rail

    def __init__(self, dataModel):
        super().__init__()
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self._row_ys = []
        self._y_to_line = {}
        self._node_half_height = 15
        self._rightmost_x = 0
        self._rail_x = 100  # overridden in createScene once the rightmost node is known
        self._highlighted_edges = []
        # Partition headers ("Main", "Subordinate #N") drawn as overlays via
        # drawForeground rather than as scene items, to avoid the same Qt
        # quirk that made the DCT box vanish on click in textView (see
        # TextScene._prepareDocFunctionOverlay). Each entry: (label, QRectF).
        self._partition_headers = []
        self.createScene()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, si.NodeItem):
            self.nodes[item.node_id] = item

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        clicked = None
        for it in self.items(event.scenePos()):
            owner = self._enclosingTarget(it)
            if owner is not None:
                clicked = owner
                break
        self._clearHighlights()
        if isinstance(clicked, si.LaneEdgeItem):
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
                    if isinstance(e, si.LaneEdgeItem) and e.source is node]
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
            if isinstance(it, si.LaneEdgeItem) and it.link is link:
                it.setHighlighted(True)
                self._highlighted_edges = [it]
                return

    @staticmethod
    def _enclosingTarget(item):
        while item is not None:
            if isinstance(item, (si.LaneEdgeItem, si.NodeItem)):
                return item
            item = item.parentItem()
        return None

    def _clearHighlights(self):
        for e in self._highlighted_edges:
            e.setHighlighted(False)
        self._highlighted_edges = []

    # ------- Geometry helpers (used by LaneEdgeItem / LaneEdgePlanner) -------

    def _computeRowGeometry(self):
        ys = sorted({round(n.pos().y(), 3) for n in self.nodes.values()})
        self._row_ys = ys
        self._y_to_line = {y: i for i, y in enumerate(ys)}
        sample = next(iter(self.nodes.values()), None)
        if sample is not None:
            self._node_half_height = sample.rect().height() / 2
        # Rightmost edge of any node, used to anchor the edge routing rail.
        self._rightmost_x = max(
            (n.pos().x() + n.rect().width() / 2 for n in self.nodes.values()),
            default=0,
        )

    def lineOfNode(self, node_item):
        y = round(node_item.pos().y(), 3)
        idx = self._y_to_line.get(y)
        if idx is not None:
            return idx
        # Fallback (e.g. after dragging): nearest row.
        if not self._row_ys:
            return 0
        return min(range(len(self._row_ys)), key=lambda i: abs(self._row_ys[i] - y))

    def gutterY(self, gutter_idx, track):
        if gutter_idx == 0:
            gutter_top = self._row_ys[0] - self._node_half_height - self._top_gutter_height
        else:
            gutter_top = self._row_ys[gutter_idx - 1] + self._node_half_height
        return gutter_top + self._gutter_padding + (track + 0.5) * self._track_spacing

    def railX(self, track):
        return self._rail_x + (track + 0.5) * self._track_spacing

    def isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def isCreationTimeLink(self, link):
        return self.isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self.isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def _headerFont(self):
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font

    def _nodeText(self, node, use_phrase):
        if isinstance(node, Instance.Instance):
            return si.decodeText(self._graph.events[node.event].stem)
        if isinstance(node, TimeX.TimeX):
            return si.decodeText(node.phrase if use_phrase else node.value)
        return ""

    def _nodeLabelFont(self):
        # Matches sceneItems.NodeItem's label font, for width measurement.
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        return font

    # TLINK relation types interpreted as "the start_node (A) happens before the related_to_node (B)".
    _A_BEFORE_B = {"BEFORE", "IBEFORE", "INCLUDES", "DURING_INV", "BEGINS", "ENDED_BY"}
    # ...and the inverse: related_to_node (B) happens before start_node (A).
    _B_BEFORE_A = {"AFTER", "IAFTER", "IS_INCLUDED", "DURING", "ENDS", "BEGUN_BY"}
    # Relations that additionally force A and B to be consecutive in the layout
    # (share a boundary in point algebra), with A immediately before B.
    # IBEFORE / IAFTER share a boundary head-to-tail (A+ = B- / A- = B+);
    # BEGINS / BEGUN_BY / ENDS / ENDED_BY share a boundary side-by-side.
    _ADJACENT_A_FIRST = {"BEGINS", "ENDED_BY", "IBEFORE"}
    # ...and the inverse: B immediately before A.
    _ADJACENT_B_FIRST = {"BEGUN_BY", "ENDS", "IAFTER"}

    def _sortNodesChronologically(self, nodes):
        """Reorder nodes by temporal precedence derived from TLINKs.

        BEFORE/IBEFORE/INCLUDES/DURING_INV/BEGINS/ENDED_BY pull the start_node earlier;
        AFTER/IAFTER/IS_INCLUDED/DURING/ENDS/BEGUN_BY pull the related_to_node earlier.
        SIMULTANEOUS/IDENTITY leave the relative order unconstrained.

        BEGINS/BEGUN_BY/ENDS/ENDED_BY/IBEFORE/IAFTER additionally cluster the
        two endpoints so they end up adjacent in the timeline, in the order
        given by the relation. They all share a boundary in point algebra
        (BEGINS/ENDS pin a side together; IBEFORE/IAFTER pin head-to-tail).

        The Document Creation Time is included as a hidden anchor so chains
        like A BEFORE DCT + DCT BEFORE B propagate to A < B even when the
        partition has no direct TLINKs between A and B.

        Original order is used as a tie-breaker. When the order graph contains
        a cycle (inconsistent annotation in the corpus), only the nodes in the
        offending strongly-connected component lose their derived order; the
        rest of the graph keeps it (see _safeTopoSort).
        """
        visible_ids = [n.get_id_str() for n in nodes]
        visible_set = set(visible_ids)
        id_to_node = {n.get_id_str(): n for n in nodes}
        anchor_ids = {n.get_id_str() for n in self._graph.nodes.values()
                      if self.isCreationTimeTimex3(n)}
        relevant_ids = visible_set | anchor_ids

        order_graph = nx.DiGraph()
        order_graph.add_nodes_from(relevant_ids)
        adjacency_pairs = []  # (first, second) - must end up consecutive
        for link in self._graph.links.values():
            if link.link_tag != "TLINK":
                continue
            a, b = link.start_node, link.related_to_node
            if a not in relevant_ids or b not in relevant_ids:
                continue
            rel = link.rel_type
            if rel in self._A_BEFORE_B:
                order_graph.add_edge(a, b)
            elif rel in self._B_BEFORE_A:
                order_graph.add_edge(b, a)
            # Only cluster when both endpoints are visible; DCT anchors are not
            # rendered, so clustering with them would create a hole.
            if a in visible_set and b in visible_set:
                if rel in self._ADJACENT_A_FIRST:
                    adjacency_pairs.append((a, b))
                elif rel in self._ADJACENT_B_FIRST:
                    adjacency_pairs.append((b, a))

        order_index = {nid: i for i, nid in enumerate(visible_ids)}
        for nid in anchor_ids - visible_set:
            order_index[nid] = len(visible_ids)  # anchors lose ties to visible nodes

        # Union-find: group every pair that must be adjacent.
        parent = {nid: nid for nid in relevant_ids}

        def find(x):
            root = x
            while parent[root] != root:
                root = parent[root]
            while parent[x] != root:
                parent[x], x = root, parent[x]
            return root

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for a, b in adjacency_pairs:
            union(a, b)

        groups = {}
        for nid in relevant_ids:
            groups.setdefault(find(nid), []).append(nid)

        # Local order inside each group: apply adjacency edges only, tie-break by original index.
        local_orders = {}
        for rep, members in groups.items():
            if len(members) == 1:
                local_orders[rep] = members
                continue
            local_g = nx.DiGraph()
            local_g.add_nodes_from(members)
            member_set = set(members)
            for first, second in adjacency_pairs:
                if first in member_set and second in member_set:
                    local_g.add_edge(first, second)
            local_orders[rep] = self._safeTopoSort(local_g, order_index)

        # Build super-graph: one node per group, aggregate cross-group temporal edges.
        super_graph = nx.DiGraph()
        super_graph.add_nodes_from(groups.keys())
        for u, v in order_graph.edges():
            ru, rv = find(u), find(v)
            if ru != rv:
                super_graph.add_edge(ru, rv)

        super_index = {rep: min(order_index[m] for m in members) for rep, members in groups.items()}
        super_ordered = self._safeTopoSort(super_graph, super_index)

        final_order = []
        for rep in super_ordered:
            final_order.extend(local_orders[rep])
        return [id_to_node[nid] for nid in final_order if nid in visible_set]

    @staticmethod
    def _safeTopoSort(g, key):
        """Topological sort that survives cycles via strongly-connected components.

        When the graph has at least one cycle (typically caused by an
        inconsistent corpus annotation, see ES100042.xml.tml with
        t1-INCLUDES-ei7-INCLUDES-ei6-ENDS-t1), a normal toposort raises
        NetworkXUnfeasible and drops every derived order. Here we instead
        condense each strongly connected component into a single super-node,
        toposort the resulting directed acyclic graph, and emit the members of
        each strongly connected component in document order. Only nodes
        actually trapped in a cycle lose their TLINK-derived position; the
        rest of the graph keeps its ordering.
        """
        try:
            return list(nx.lexicographical_topological_sort(g, key=lambda n: key[n]))
        except nx.NetworkXUnfeasible:
            sccs = list(nx.strongly_connected_components(g))
            cond = nx.condensation(g, sccs)
            cond_key = {n: min(key[m] for m in cond.nodes[n]['members']) for n in cond.nodes}
            cond_order = list(nx.lexicographical_topological_sort(cond, key=lambda n: cond_key[n]))
            result = []
            for scc_idx in cond_order:
                members = sorted(cond.nodes[scc_idx]['members'], key=lambda m: key[m])
                result.extend(members)
            return result

    def _computeStartTimepoints(self, partition):
        """Returns {node_id: start_timepoint_int} from TLEX's TCSP solver.

        Each event/timex is decomposed by pyTLEX into two time points (xxx_minus,
        xxx_plus) and Z3 assigns integers so simultaneous points share the same
        integer. We keep only the 'minus' (start) entries: the partition layout
        will place nodes in columns by start integer and stack co-starting nodes
        vertically. Returns None on inconsistency or solver failure.
        """
        try:
            solved = find_timeline(partition)
        except Exception:
            return None
        if solved is None:
            return None
        result = {}
        for tp_str, entries in solved.items():
            try:
                tp = int(tp_str)
            except (TypeError, ValueError):
                continue
            for entry in entries:
                node_id, _, boundary = entry.rpartition('_')
                if boundary == 'minus':
                    result[node_id] = tp
        return result

    def _drawPartitions(self, partitions, kind, line, use_phrase, graphModel, header_x):
        for displayed_idx, (partition, visible_nodes) in enumerate(partitions, 1):
            line = self._drawPartition(partition, visible_nodes, kind, displayed_idx,
                                       line, use_phrase, graphModel, header_x)
        return line

    def _drawPartition(self, partition, visible_nodes, kind, displayed_idx,
                       line, use_phrase, graphModel, header_x):
        """One partition: events ordered left-to-right by start timepoint,
        simultaneous starts stacked vertically. Falls back to a single row
        when TLEX cannot solve the partition (inconsistent annotation).
        """
        tp_map = self._computeStartTimepoints(partition)
        if tp_map is not None:
            by_tp = defaultdict(list)
            untimed = []
            for node in visible_nodes:
                tp = tp_map.get(node.get_id_str())
                if tp is None:
                    untimed.append(node)
                else:
                    by_tp[tp].append(node)
            columns = [by_tp[tp] for tp in sorted(by_tp.keys())]
            if untimed:
                columns.append(untimed)
        else:
            ordered = self._sortNodesChronologically(visible_nodes)
            columns = [[n] for n in ordered]

        if not columns:
            return line

        # Stable stacking order inside a column = document order.
        doc_index = {n.get_id_str(): i for i, n in enumerate(visible_nodes)}
        for col in columns:
            col.sort(key=lambda n: doc_index[n.get_id_str()])

        first_node = None
        max_stack = max(len(col) for col in columns)

        for col_idx, col in enumerate(columns):
            for row_idx, node in enumerate(col):
                text = self._nodeText(node, use_phrase)
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                self.addItem(graphNode)
                if first_node is None:
                    first_node = graphNode
                # Columns share a fixed x origin across every partition (node
                # centres aligned) so the edge router's inter-column channels
                # land in clean gaps. A per-partition x_shift would offset the
                # columns slightly between partitions, making a wide node in one
                # partition stick into another partition's routing channel.
                xpos = self._x_origin + col_idx * self._horizontal_distance
                ypos = line + row_idx * self._vertical_distance
                graphNode.setPos(xpos, ypos)
                graphModel.add_node(node.get_id_str())

        # Stash the partition header for drawForeground. We don't add it as a
        # QGraphicsItem to the scene because clicking on a QGraphicsTextItem
        # (even with Qt.NoButton) triggers a Qt repaint quirk that hides it.
        label = kind if kind == "Main" else f"{kind} #{displayed_idx}"
        fm = QFontMetrics(self._headerFont())
        label_w = fm.horizontalAdvance(label)
        label_h = fm.height()
        first_node_rect = first_node.rect().translated(first_node.pos())
        label_y = first_node_rect.center().y() - label_h / 2
        self._partition_headers.append((label, QRectF(header_x, label_y, label_w, label_h)))

        line += max_stack * self._vertical_distance + self._partition_gap
        return line

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self._partition_headers:
            return
        painter.save()
        painter.setFont(self._headerFont())
        painter.setPen(Qt.darkGray)
        for label, bbox in self._partition_headers:
            if rect.intersects(bbox):
                painter.drawText(bbox, Qt.AlignLeft | Qt.AlignVCenter, label)
        painter.restore()

    def _orderedPartitions(self):
        """Returns (mains, subs) preferring the partition containing the DCT
        as main.

        TLEX's heuristic "main = largest partition" can crown a partition of
        subordinated / hypothetical / reported events as main when the
        DCT-anchored real-world events happen to form a smaller partition.
        Conceptually the paper's "main timeline" is the one anchored at the
        DCT, so we override TLEX's choice here.

        Falls back to TLEX's original ordering if there is no DCT in the
        document, or if the DCT is already in a main partition (the common
        case).
        """
        mains = list(self._tlex.main_graphs)
        subs = list(self._tlex.subordination_graphs)
        dct_id = next((nid for nid, n in self._graph.nodes.items()
                       if self.isCreationTimeTimex3(n)), None)
        if dct_id is None or any(dct_id in m.nodes for m in mains):
            return mains, subs
        for i, s in enumerate(subs):
            if dct_id in s.nodes:
                return [s], mains + subs[:i] + subs[i + 1:]
        return mains, subs

    def createScene(self):
        graphModel = nx.MultiDiGraph()
        # Use the partitions already computed (and corrected) by TLEX.
        # Calling Partitioner.partition_graph(self._graph) here would re-do
        # the work and, more importantly, expose a bug in process_output:
        # process_output assigns type="main_graph" whenever a partition is
        # larger than its immediate predecessor in DFS order, regardless of
        # the global max. TLEX.__post_init__ patches this by keeping only
        # the truly largest partition as main and demoting the rest to
        # subordinations, so we read from there directly.

        def visible_pair(partition):
            # The DCT is kept in the visible nodes so suggested_links (which by
            # construction anchor every disconnected timex to it) have a
            # rendered endpoint to terminate on.
            nodes = list(partition.nodes.values())
            return (partition, nodes) if nodes else None

        mains, subs = self._orderedPartitions()
        main_partitions = [p for p in (visible_pair(p) for p in mains) if p]
        sub_partitions = [p for p in (visible_pair(p) for p in subs) if p]

        fm = QFontMetrics(self._headerFont())
        max_header_width = 0
        if main_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Main"))
        if sub_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Subordinate #{len(sub_partitions)}"))
        header_x = -max_header_width - self._partition_label_margin

        # Widen the column pitch if any node label is wider than the default,
        # so the edge router always has a clean inter-column channel (a node
        # wider than the pitch would overlap the next column and leave no gap).
        probe = QGraphicsTextItem()
        probe.setFont(self._nodeLabelFont())
        max_node_w = 0
        for _, vis_nodes in main_partitions + sub_partitions:
            for node in vis_nodes:
                probe.setPlainText(self._nodeText(node, True))
                max_node_w = max(max_node_w, probe.boundingRect().width() - 2)
        self._horizontal_distance = max(type(self)._horizontal_distance,
                                        int(max_node_w) + 50)

        line = 0
        line = self._drawPartitions(main_partitions, "Main", line, use_phrase=True, graphModel=graphModel, header_x=header_x)
        line = self._drawPartitions(sub_partitions, "Subordinate", line, use_phrase=True, graphModel=graphModel, header_x=header_x)

        if not self.nodes:
            return

        # Edge routing: grid router that uses the inter-column / inter-row
        # channels of this view's fixed grid, instead of the single right-hand
        # rail used by textView's LaneEdgePlanner.
        self._computeRowGeometry()
        GridEdgePlanner(self, track_spacing=self._track_spacing).drawEdges()

        # Partition headers are drawn as overlays (not scene items), so we
        # extend sceneRect manually to keep them scrollable.
        if self._partition_headers:
            bbox = self.itemsBoundingRect()
            for _, hbox in self._partition_headers:
                bbox = bbox.united(hbox)
            self.setSceneRect(bbox.adjusted(-10, -10, 10, 10))


def _assignTracks(intervals):
    """Greedy interval-graph colouring. ``intervals`` is a list of
    (start, end) pairs; returns (tracks, count) where ``tracks`` is a list
    parallel to the input giving each interval a track index such that
    overlapping intervals get distinct tracks."""
    order = sorted(range(len(intervals)), key=lambda i: intervals[i][0])
    track_end = []  # track_end[t] = current right end of track t
    tracks = [0] * len(intervals)
    for i in order:
        start, end = intervals[i]
        for t in range(len(track_end)):
            if track_end[t] <= start:
                track_end[t] = end
                tracks[i] = t
                break
        else:
            tracks[i] = len(track_end)
            track_end.append(end)
    return tracks, len(track_end)


def _cluster(values, tol):
    """Groups near-equal values into clusters whose members are within ``tol``
    of their neighbours. Returns (centers, idx_of) where ``centers`` is the
    per-cluster mean and ``idx_of`` maps each input value to its cluster index.

    Needed because each partition lays its columns from its own x_shift, so the
    "same" logical column lands at slightly different x in different partitions.
    Treating every distinct x as its own column would put routing channels (the
    midpoints between columns) right on top of nodes."""
    vals = sorted(set(values))
    clusters = [[vals[0]]]
    for v in vals[1:]:
        if v - clusters[-1][-1] <= tol:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    centers = [sum(c) / len(c) for c in clusters]
    idx_of = {}
    for ci, c in enumerate(clusters):
        for v in c:
            idx_of[v] = ci
    return centers, idx_of


class GridEdgeItem(si.LaneEdgeItem):
    """Orthogonal edge routed through the grid channels of the time view.

    The time view lays nodes on a fixed grid (columns by start timepoint,
    rows by simultaneity). Instead of sending every edge to a single
    right-hand rail (LaneEdgeItem's behaviour, kept for textView), this
    routes each edge locally. Two shapes, chosen by GridEdgePlanner:

    - 'straight': source and target share a column and the column is clear
      between them -> a single vertical segment, entering both nodes
      perpendicular to their top/bottom edges. No detour, no turn.

    - 'channel': exit the source vertically with a short perpendicular stub,
      jog into the inter-column channel nearest the source, run along it
      (vertically) to the target's row band, turn into the inter-row channel
      beside the target (horizontally), and enter the target vertically.

    GridEdgePlanner precomputes ``vx`` (inter-column run) and ``hy`` (inter-row
    run) with per-channel track offsets baked in. Endpoints are recomputed here
    from live node positions so dragging still works.
    """

    _stub = 10       # length of the perpendicular exit stub
    _jog_step = 5    # extra depth per edge so sibling exit jogs don't overlap

    def updatePosition(self):
        plan = self._plan
        src, tgt = self.source, self.target
        s_rect = src.rect().translated(src.pos())
        t_rect = tgt.rect().translated(tgt.pos())
        # Attach points are spread along each node's horizontal edge (by
        # GridEdgePlanner) so endpoints sharing a side don't overlap.
        sx = s_rect.left() + plan.get('src_frac', 0.5) * s_rect.width()
        tx = t_rect.left() + plan.get('tgt_frac', 0.5) * t_rect.width()
        sy = src.pos().y()
        ty = tgt.pos().y()
        path = QPainterPath()

        if plan.get('mode') == 'straight':
            down = ty >= sy
            sy_exit = s_rect.bottom() if down else s_rect.top()
            ty_entry = t_rect.top() if down else t_rect.bottom()
            path.moveTo(sx, sy_exit)
            if abs(tx - sx) < 1.0:
                path.lineTo(tx, ty_entry)
            else:
                midy = (sy_exit + ty_entry) / 2
                path.lineTo(sx, midy)
                path.lineTo(tx, midy)
                path.lineTo(tx, ty_entry)
            self._drawArrow(path, tx, ty_entry, math.pi / 2 if down else -math.pi / 2)
            self.setPath(path)
            self._placeLabel((sx + tx) / 2, (sy_exit + ty_entry) / 2)
            return

        vx = plan['vx']
        hy = plan['hy']
        # Stagger the exit-jog depth by rank so edges leaving the same node
        # side don't run their horizontal jog at the same y (which overlaps).
        depth = self._stub + plan.get('src_jog', 0) * self._jog_step
        if hy >= sy:
            sy_exit = s_rect.bottom()
            stub_y = min(sy_exit + depth, hy)
        else:
            sy_exit = s_rect.top()
            stub_y = max(sy_exit - depth, hy)
        if hy <= ty:
            ty_entry = t_rect.top()
            arrow_angle = math.pi / 2
        else:
            ty_entry = t_rect.bottom()
            arrow_angle = -math.pi / 2

        path.moveTo(sx, sy_exit)
        path.lineTo(sx, stub_y)       # perpendicular exit stub
        path.lineTo(vx, stub_y)       # jog into the inter-column channel
        path.lineTo(vx, hy)           # run down/up the inter-column channel
        path.lineTo(tx, hy)           # turn, run along the inter-row channel
        path.lineTo(tx, ty_entry)     # perpendicular entry into the target
        self._drawArrow(path, tx, ty_entry, arrow_angle)
        self.setPath(path)
        self._placeLabel(vx, (stub_y + hy) / 2)

    def _placeLabel(self, cx, cy):
        rect = self.label.boundingRect()
        lx = cx + self._label_margin
        ly = cy - rect.height() / 2
        self.label.setPos(lx, ly)
        if getattr(self, '_label_bg', None) is not None:
            m = self._label_margin
            self._label_bg.setRect(lx - m, ly - m,
                                   rect.width() + 2 * m, rect.height() + 2 * m)


class GridEdgePlanner:
    """Builds grid-routed edges for the time view.

    Columns and rows are derived by clustering node x/y positions (see
    _cluster). Inter-column channels run vertically, centred between adjacent
    column clusters; inter-row channels run horizontally, centred between
    adjacent row clusters. For each edge it picks the inter-column channel
    adjacent to the source (toward the target) and the inter-row channel
    adjacent to the target (toward the source), then assigns per-channel tracks
    so parallel edges in the same channel don't overlap. Same-column edges with
    a clear path skip channels entirely and run straight.
    """

    def __init__(self, scene, track_spacing=6):
        self.scene = scene
        self.track_spacing = track_spacing

    def drawEdges(self):
        s = self.scene
        nodes = list(s.nodes.values())
        if not nodes:
            return
        node_xs = [round(n.pos().x(), 3) for n in nodes]
        node_ys = [round(n.pos().y(), 3) for n in nodes]
        H = s._horizontal_distance
        V = s._vertical_distance
        col_centers, col_of = _cluster(node_xs, H * 0.5)
        row_centers, row_of = _cluster(node_ys, V * 0.45)

        # Actual outer node edges per cluster, so a channel sits in the real
        # empty gap. Using cluster-centre +/- max-half-width is wrong because
        # the centre is the mean of member x's (which differ per partition by
        # x_shift), so a node at the cluster's far edge can stick out past it.
        col_right, col_left = {}, {}
        row_bottom, row_top = {}, {}
        for n in nodes:
            r = n.rect().translated(n.pos())
            ci = col_of[round(n.pos().x(), 3)]
            ri = row_of[round(n.pos().y(), 3)]
            col_right[ci] = max(col_right.get(ci, -1e18), r.right())
            col_left[ci] = min(col_left.get(ci, 1e18), r.left())
            row_bottom[ri] = max(row_bottom.get(ri, -1e18), r.bottom())
            row_top[ri] = min(row_top.get(ri, 1e18), r.top())

        MARGIN = 5

        def _vbounds(left):
            # Empty span between the rightmost node edge of cluster `left` and
            # the leftmost node edge of cluster left+1.
            return col_right[left] + MARGIN, col_left[left + 1] - MARGIN

        def _hbounds(top):
            return row_bottom[top] + MARGIN, row_top[top + 1] - MARGIN

        def vchan_x(left):
            # Centre of the actual empty gap (not the midpoint of column
            # centres), so a wide node on one side doesn't get crossed.
            if left < 0:
                return col_centers[0] - H / 2
            if left >= len(col_centers) - 1:
                return col_centers[-1] + H / 2
            lo, hi = _vbounds(left)
            if hi <= lo:
                return (col_centers[left] + col_centers[left + 1]) / 2
            return (lo + hi) / 2

        def hchan_y(top):
            if top < 0:
                return row_centers[0] - V / 2
            if top >= len(row_centers) - 1:
                return row_centers[-1] + V / 2
            lo, hi = _hbounds(top)
            if hi <= lo:
                return (row_centers[top] + row_centers[top + 1]) / 2
            return (lo + hi) / 2

        def vgap(left):
            if 0 <= left < len(col_centers) - 1:
                lo, hi = _vbounds(left)
                return max(8.0, hi - lo)
            return H * 0.6

        def hgap(top):
            if 0 <= top < len(row_centers) - 1:
                lo, hi = _hbounds(top)
                return max(8.0, hi - lo)
            return V * 0.6

        def vertical_clear(x, ya, yb, src, tgt):
            lo, hi = min(ya, yb), max(ya, yb)
            for n in nodes:
                if n is src or n is tgt:
                    continue
                r = n.rect().translated(n.pos())
                if r.left() - 2 <= x <= r.right() + 2 and r.bottom() > lo + 1 and r.top() < hi - 1:
                    return False
            return True

        annotated = [v for v in s._graph.links.values() if not s.isCreationTimeLink(v)]
        suggested = getattr(s._tlex, 'suggested_links', None) or []
        candidates = [(v, False) for v in annotated] + [(v, True) for v in suggested]

        routes = []
        for link, is_suggested in candidates:
            src = s.nodes.get(link.start_node)
            tgt = s.nodes.get(link.related_to_node)
            if src is None or tgt is None or src is tgt:
                continue
            sx = round(src.pos().x(), 3)
            sy = round(src.pos().y(), 3)
            tx = round(tgt.pos().x(), 3)
            ty = round(tgt.pos().y(), 3)
            cs, ct = col_of[sx], col_of[tx]
            date_inferred = getattr(link, '_date_inferred', False)
            route = {
                'link': link, 'src': src, 'tgt': tgt, 'suggested': is_suggested,
                'date_inferred': date_inferred,
                'sx': sx, 'sy': sy, 'tx': tx, 'ty': ty,
                'color': si.linkColor(link, date_inferred), 'text': link.rel_type,
                'mode': 'channel',
            }

            s_rect = src.rect().translated(src.pos())
            t_rect = tgt.rect().translated(tgt.pos())
            down = ty >= sy
            y_from = s_rect.bottom() if down else s_rect.top()
            y_to = t_rect.top() if down else t_rect.bottom()
            if cs == ct and vertical_clear(sx, y_from, y_to, src, tgt):
                route['mode'] = 'straight'
            else:
                # Inter-column channel: adjacent to the source, toward target.
                if ct > cs:
                    v_left = cs
                elif ct < cs:
                    v_left = cs - 1
                else:
                    v_left = cs if cs < len(col_centers) - 1 else cs - 1
                rs, rt = row_of[sy], row_of[ty]
                # Inter-row channel: adjacent to the target, toward the source.
                if rs < rt:
                    h_top = rt - 1
                elif rs > rt:
                    h_top = rt
                else:
                    h_top = rt - 1 if rt > 0 else rt
                route['v_left'] = v_left
                route['vx_base'] = vchan_x(v_left)
                route['h_top'] = h_top
                route['hy_base'] = hchan_y(h_top)
            routes.append(route)

        channel_routes = [r for r in routes if r['mode'] == 'channel']
        self._allocate(channel_routes, key='v_left', base='vx_base', final='vx',
                       span=lambda r: (min(r['sy'], r['hy_base']), max(r['sy'], r['hy_base'])),
                       gap_of=vgap)
        self._allocate(channel_routes, key='h_top', base='hy_base', final='hy',
                       span=lambda r: (min(r['vx'], r['tx']), max(r['vx'], r['tx'])),
                       gap_of=hgap)

        self._spreadAttachments(routes)

        for r in routes:
            plan = {'link': r['link'], 'suggested': r['suggested'], 'mode': r['mode'],
                    'date_inferred': r['date_inferred'],
                    'src_frac': r['src_frac'], 'tgt_frac': r['tgt_frac']}
            if r['mode'] == 'channel':
                plan['vx'] = r['vx']
                plan['hy'] = r['hy']
                plan['src_jog'] = r.get('src_jog', 0)
            edge = GridEdgeItem(r['src'], r['tgt'], scene_ref=s, plan=plan,
                                text=r['text'], text_color=QColor(145, 145, 0),
                                link_color=r['color'])
            s.addItem(edge)

    @staticmethod
    def _endpoint(route, which):
        """Returns (node, side, lead_x) for the src/tgt endpoint of a route.
        ``side`` is 'top'/'bottom'; ``lead_x`` is the x the edge heads toward
        (src) or comes from (tgt), used to order attachments and reduce
        crossings near the node."""
        if route['mode'] == 'straight':
            down = route['ty'] >= route['sy']
            if which == 'src':
                return route['src'], ('bottom' if down else 'top'), route['tx']
            return route['tgt'], ('top' if down else 'bottom'), route['sx']
        hy, vx = route['hy'], route['vx']
        if which == 'src':
            return route['src'], ('bottom' if hy >= route['sy'] else 'top'), vx
        return route['tgt'], ('top' if hy <= route['ty'] else 'bottom'), vx

    def _spreadAttachments(self, routes):
        """Distribute edge endpoints across each node's top/bottom edge so they
        don't overlap. Within a (node, side) group, endpoints are ordered by
        the x they lead to/from and placed left-to-right at fractions
        1/(n+1) .. n/(n+1) of the node width (a single endpoint stays centred,
        keeping straight edges vertical)."""
        groups = defaultdict(list)
        for r in routes:
            for which in ('src', 'tgt'):
                node, side, lead = self._endpoint(r, which)
                groups[(id(node), side)].append((lead, r['link'].get_id_str(), r, which))
        for items in groups.values():
            items.sort(key=lambda t: (t[0], t[1]))
            n = len(items)
            jog = 0
            for i, (_, _, r, which) in enumerate(items):
                r[which + '_frac'] = (i + 1) / (n + 1)
                # Channel edges leaving this side get a staggered jog depth so
                # their short horizontal exit jogs don't land on the same y.
                if which == 'src' and r['mode'] == 'channel':
                    r['src_jog'] = jog
                    jog += 1

    def _allocate(self, routes, key, base, final, span, gap_of):
        """Assign tracks within each channel (grouped by ``key``) and bake the
        track offset into an absolute coordinate stored under ``final``. Tracks
        are centred on the channel's base coordinate, but the spacing is reduced
        when needed so the whole bundle fits inside the channel's empty gap
        (``gap_of(key)``) rather than spilling over the neighbouring nodes."""
        groups = defaultdict(list)
        for r in routes:
            groups[r[key]].append(r)
        for gkey, group in groups.items():
            intervals = [span(r) for r in group]
            tracks, count = _assignTracks(intervals)
            spacing = self.track_spacing
            if count > 1:
                spacing = min(spacing, gap_of(gkey) / (count - 1))
            for r, t in zip(group, tracks):
                offset = (t - (count - 1) / 2) * spacing
                r[final] = r[base] + offset
