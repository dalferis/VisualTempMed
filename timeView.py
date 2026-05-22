from collections import defaultdict
import networkx as nx
import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from pytlex_core.timeline.Timeline import find_timeline
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PySide6.QtGui import QFont, QFontMetrics, QPainter
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
    _horizontal_distance = 150
    _vertical_distance = 80
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
        # TextScene._prepareDctOverlay). Each entry: (label, QRectF).
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
        x_shift = 0
        max_stack = max(len(col) for col in columns)

        for col_idx, col in enumerate(columns):
            for row_idx, node in enumerate(col):
                if isinstance(node, Instance.Instance):
                    text = si.decodeText(self._graph.events[node.event].stem)
                elif isinstance(node, TimeX.TimeX):
                    text = si.decodeText(node.phrase if use_phrase else node.value)
                else:
                    text = ""
                graphNode = si.NodeItem(node.get_id_str(), text=text)
                self.addItem(graphNode)
                if first_node is None:
                    first_node = graphNode
                    x_shift = graphNode.rect().width() / 2
                xpos = x_shift + col_idx * self._horizontal_distance
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

        line = 0
        line = self._drawPartitions(main_partitions, "Main", line, use_phrase=True, graphModel=graphModel, header_x=header_x)
        line = self._drawPartitions(sub_partitions, "Subordinate", line, use_phrase=True, graphModel=graphModel, header_x=header_x)

        if not self.nodes:
            return

        # Edge routing setup: row geometry + rail position to the right of the
        # rightmost node so cross_line edges don't pile up over the headers
        # column on the left.
        self._computeRowGeometry()
        self._rail_x = self._rightmost_x + self._rail_margin
        si.LaneEdgePlanner(self,
                           track_spacing=self._track_spacing,
                           gutter_padding=self._gutter_padding).drawEdges()

        # Partition headers are drawn as overlays (not scene items), so we
        # extend sceneRect manually to keep them scrollable.
        if self._partition_headers:
            bbox = self.itemsBoundingRect()
            for _, hbox in self._partition_headers:
                bbox = bbox.united(hbox)
            self.setSceneRect(bbox.adjusted(-10, -10, 10, 10))
