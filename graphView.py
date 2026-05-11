from collections import defaultdict
import networkx as nx
import sceneItems as si
from pytlex_core.algorithms import TLEX
from pytlex_core.data import Graph, Instance, TimeX
from pytlex_core.timeline.Timeline import find_timeline
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtCore import Qt, Signal


class GraphView(QGraphicsView):
    def __init__(self, model):
        self.scene = GraphScene(model)
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

class GraphScene(QGraphicsScene):
    nodeClicked = Signal(str)

    _graph: Graph.Graph
    _tlex: TLEX.TLEX

    _max_columns = 15
    _horizontal_distance = 150
    _vertical_distance = 80
    _partition_gap = 40  # extra vertical space between successive partitions
    _partition_label_margin = 12  # horizontal gap between partition header and first node

    def __init__(self, dataModel):
        super().__init__()
        self._graph = dataModel.graph()
        self._tlex = dataModel.tlex()
        self.nodes = {}
        self.createScene()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, si.NodeItem):
            self.nodes[item.node_id] = item

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        for it in self.items(event.scenePos()):
            owner = it
            while owner is not None and not isinstance(owner, si.NodeItem):
                owner = owner.parentItem()
            if isinstance(owner, si.NodeItem):
                self.nodeClicked.emit(owner.node_id)
                return

    def isCreationTimeTimex3(self, timex3):
        return isinstance(timex3, TimeX.TimeX) and hasattr(timex3, "documentFunction") and timex3.documentFunction.upper() == "CREATION_TIME"

    def isCreationTimeLink(self, link):
        return self.isCreationTimeTimex3(self._graph.nodes[link.start_node]) or self.isCreationTimeTimex3(self._graph.nodes[link.related_to_node])

    def _headerFont(self):
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font

    # TLINK relation types interpreted as "the start_node happens before the related_to_node".
    _A_BEFORE_B = {"BEFORE", "IBEFORE", "INCLUDES", "DURING_INV", "BEGINS", "ENDED_BY"}
    # ...and the inverse: related_to_node happens before start_node.
    _B_BEFORE_A = {"AFTER", "IAFTER", "IS_INCLUDED", "DURING", "ENDS", "BEGUN_BY"}
    # Relations that additionally force A and B to be consecutive in the layout
    # (share a boundary), with A immediately before B.
    _ADJACENT_A_FIRST = {"BEGINS", "ENDED_BY"}
    # ...and the inverse: B immediately before A.
    _ADJACENT_B_FIRST = {"BEGUN_BY", "ENDS"}

    def _sortNodesChronologically(self, nodes):
        """Reorder nodes by temporal precedence derived from TLINKs.

        BEFORE/IBEFORE/INCLUDES/DURING_INV/BEGINS/ENDED_BY pull the start_node earlier;
        AFTER/IAFTER/IS_INCLUDED/DURING/ENDS/BEGUN_BY pull the related_to_node earlier.
        SIMULTANEOUS/IDENTITY leave the relative order unconstrained.

        BEGINS/BEGUN_BY/ENDS/ENDED_BY additionally cluster the two endpoints so
        they end up adjacent in the timeline, in the order given by the relation.

        The Document Creation Time is included as a hidden anchor so chains
        like A BEFORE DCT + DCT BEFORE B propagate to A < B even when the
        partition has no direct TLINKs between A and B.

        Original order is used as a tie-breaker. On cycle detection (inconsistent
        annotation) the original order is kept.
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
            try:
                local_orders[rep] = list(nx.lexicographical_topological_sort(local_g, key=lambda nid: order_index[nid]))
            except nx.NetworkXUnfeasible:
                local_orders[rep] = sorted(members, key=lambda nid: order_index[nid])

        # Build super-graph: one node per group, aggregate cross-group temporal edges.
        super_graph = nx.DiGraph()
        super_graph.add_nodes_from(groups.keys())
        for u, v in order_graph.edges():
            ru, rv = find(u), find(v)
            if ru != rv:
                super_graph.add_edge(ru, rv)

        super_index = {rep: min(order_index[m] for m in members) for rep, members in groups.items()}
        try:
            super_ordered = list(nx.lexicographical_topological_sort(super_graph, key=lambda rep: super_index[rep]))
        except nx.NetworkXUnfeasible:
            super_ordered = sorted(groups.keys(), key=lambda rep: super_index[rep])

        final_order = []
        for rep in super_ordered:
            final_order.extend(local_orders[rep])
        return [id_to_node[nid] for nid in final_order if nid in visible_set]

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

        header = QGraphicsTextItem(f"{kind} #{displayed_idx}")
        header.setFont(self._headerFont())
        header.setDefaultTextColor(Qt.darkGray)
        header.setAcceptedMouseButtons(Qt.NoButton)
        self.addItem(header)
        header_rect = header.boundingRect()
        first_node_rect = first_node.rect().translated(first_node.pos())
        header.setPos(
            header_x,
            first_node_rect.center().y() - header_rect.height() / 2,
        )

        line += max_stack * self._vertical_distance + self._partition_gap
        return line

    def createScene(self):
        graphModel = nx.MultiDiGraph()
        partition_graph = TLEX.Partitioner.partition_graph(self._graph)

        def visible_pair(partition):
            nodes = [v for v in partition.nodes.values() if not self.isCreationTimeTimex3(v)]
            return (partition, nodes) if nodes else None

        main_partitions = [p for p in (visible_pair(p) for p in partition_graph["main_graphs"]) if p]
        sub_partitions = [p for p in (visible_pair(p) for p in partition_graph["subordination_graphs"]) if p]

        fm = QFontMetrics(self._headerFont())
        max_header_width = 0
        if main_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Main #{len(main_partitions)}"))
        if sub_partitions:
            max_header_width = max(max_header_width, fm.horizontalAdvance(f"Subordinate #{len(sub_partitions)}"))
        header_x = -max_header_width - self._partition_label_margin

        line = 0
        line = self._drawPartitions(main_partitions, "Main", line, use_phrase=True, graphModel=graphModel, header_x=header_x)
        line = self._drawPartitions(sub_partitions, "Subordinate", line, use_phrase=False, graphModel=graphModel, header_x=header_x)

        linklist = [v for v in self._graph.links.values() if not self.isCreationTimeLink(v)] + [v for v in self._tlex.s_links if not self.isCreationTimeLink(v)]
        linklist.sort(key=lambda x: (x.start_node, x.related_to_node))
        linklistlist = [[linklist[0]]]
        for link in linklist[1:]:
            if link.start_node == linklistlist[-1][-1].start_node and link.related_to_node == linklistlist[-1][-1].related_to_node:
                linklistlist[-1].append(link)
            else:
                linklistlist.append([link])

        for llist in linklistlist:
            nlinks = len(llist) // 2
            for link in llist:
                graphModel.add_edge(link.start_node, link.related_to_node)
                start_node = self.nodes.get(link.start_node, None)
                end_node = self.nodes.get(link.related_to_node, None)
                if not start_node is None and not end_node is None:
                    color = Qt.black if link.link_tag == "TLINK" else Qt.red if link.link_tag == "SLINK" else Qt.blue
                    edgeitem = si.EdgeItem(start_node, end_node, text=link.rel_type, text_color = QColor(color).darker(150), link_color = color, curvature=0.2*nlinks)
                    self.addItem(edgeitem)
                    nlinks -= 1
