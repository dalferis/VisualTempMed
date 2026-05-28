"""
Date-derived ordering links for the time view.

TLEX/Z3 orders nodes purely from the annotated TLINKs; it never looks at the
TIMEX3 ``value`` attribute. So two dated timexes with no TLINK between them are
left unordered (e.g. "today"/"Yesterday" landing in the same column even though
their dates differ). This module infers extra TLINKs from comparable TIMEX3
dates and feeds them to the solver, which both orders the timexes and, by
propagating through the existing links, repositions the events anchored to them.

Design (agreed for v1):
  - Compare every TIMEX3 of the document with a concrete 4-digit year
    (plain YYYY[-MM[-DD]], all digits); skip XXXX, refs, weeks/seasons/quarters,
    DURATION/SET.
  - Only BEFORE and SIMULTANEOUS relations (no INCLUDES yet). Prefix-equal
    values of different granularity (containment) are skipped.
  - Validate per partition with an exact Z3 point-algebra model, incrementally
    via union-find: a partition whose annotation is already inconsistent
    (base-UNSAT) only blocks itself.
  - A date link may merge two partitions, EXCEPT when it would pull
    non-factual subordinated content (subordinated by a MODAL / CONDITIONAL /
    COUNTER_FACTIVE / NEG_EVIDENTIAL SLINK) onto a shared timeline. Crossing
    into EVIDENTIAL / FACTIVE subordinated content, or merging merely
    disconnected partitions, is allowed.

The returned links are real ``Link`` objects (link_tag "TLINK") flagged with
``_date_inferred = True`` so the views can draw them in a distinct style and
downstream consumers can tell them from annotated links.
"""
import re
import z3
from pytlex_core.data import Graph, TimeX, Link
from pytlex_core.algorithms import TLEX, Partitioner

# SLINK types whose subordinated content is "factual enough" to place on a
# shared timeline. The rest are non-factual: a date link must not merge them.
_FACTUAL_SAFE_SLINK = {"EVIDENTIAL", "FACTIVE"}

_DATE_RE = re.compile(r'\d{4}(-\d{1,2}(-\d{1,2})?)?$')


def _date_key(timex):
    """Comparable (year[, month[, day]]) tuple for a TIMEX3 with a concrete
    4-digit-year DATE/TIME value, else None."""
    if getattr(timex, 'type', None) not in ('DATE', 'TIME'):
        return None
    value = getattr(timex, 'value', None)
    if not value:
        return None
    date_part = value.split('T')[0]
    if not _DATE_RE.fullmatch(date_part):
        return None
    return tuple(int(x) for x in date_part.split('-'))


def _relation(k1, k2):
    """'BEFORE' / 'AFTER' / 'SIMULTANEOUS' / 'CONTAINS' between two date keys."""
    n = min(len(k1), len(k2))
    if k1[:n] != k2[:n]:
        return 'BEFORE' if k1[:n] < k2[:n] else 'AFTER'
    if len(k1) == len(k2):
        return 'SIMULTANEOUS'
    return 'CONTAINS'   # prefix-equal, different granularity -> INCLUDES (skip v1)


def _add(solver, points, a, rel, b):
    """Adds the point-algebra constraints for one TLINK (start=a, related=b)."""
    (am, ap), (bm, bp) = points(a), points(b)
    if rel == 'BEFORE':         solver.add(ap < bm)
    elif rel == 'AFTER':        solver.add(bp < am)
    elif rel == 'IBEFORE':      solver.add(ap == bm)
    elif rel == 'IAFTER':       solver.add(bp == am)
    elif rel == 'INCLUDES':     solver.add(am < bm, bp < ap)
    elif rel == 'IS_INCLUDED':  solver.add(bm < am, ap < bp)
    elif rel == 'DURING':       solver.add(bm <= am, ap <= bp)
    elif rel == 'DURING_INV':   solver.add(am <= bm, bp <= ap)
    elif rel in ('SIMULTANEOUS', 'IDENTITY'): solver.add(am == bm, ap == bp)
    elif rel == 'BEGINS':       solver.add(am == bm, ap < bp)
    elif rel == 'BEGUN_BY':     solver.add(am == bm, bp < ap)
    elif rel == 'ENDS':         solver.add(ap == bp, bm < am)
    elif rel == 'ENDED_BY':     solver.add(ap == bp, am < bm)


def _sat(triples):
    """True if the set of (start, relType, related) TLINK triples is
    point-algebra consistent."""
    solver = z3.Solver()
    pts = {}
    def points(n):
        if n not in pts:
            m, p = z3.Int(n + '_m'), z3.Int(n + '_p')
            solver.add(m < p)
            pts[n] = (m, p)
        return pts[n]
    for a, rel, b in triples:
        _add(solver, points, a, rel, b)
    return solver.check() == z3.sat


def infer_date_links(graph):
    """Returns a list of date-derived TLINK ``Link`` objects (flagged with
    ``_date_inferred = True``) to add to ``graph.links`` before partitioning."""
    Partitioner.single_links.clear()
    try:
        tlex = TLEX.TLEX(graph=graph)
    except Exception:
        return []
    parts = list(tlex.main_graphs) + list(tlex.subordination_graphs)
    if not parts:
        return []
    part_of = {nid: i for i, p in enumerate(parts) for nid in p.nodes}

    # Annotated TLINK triples per original partition + base consistency.
    triples = {i: [] for i in range(len(parts))}
    for link in graph.links.values():
        if link.link_tag == 'TLINK' and link.start_node in part_of:
            triples[part_of[link.start_node]].append(
                (link.start_node, link.rel_type, link.related_to_node))
    base_sat = {i: _sat(triples[i]) for i in range(len(parts))}

    # Partitions holding the subordinated side of a non-factual single SLINK.
    nonfactual = set()
    for sl in (tlex.s_links or []):
        if sl.rel_type in _FACTUAL_SAFE_SLINK:
            continue
        sub = sl.related_to_node           # subordinatedEventInstance
        if sub in part_of and sl.start_node in part_of \
                and part_of[sub] != part_of[sl.start_node]:
            nonfactual.add(part_of[sub])

    # Pairs already related by an annotated TLINK (either direction). A date
    # link between such a pair would only duplicate an existing relation (and
    # draw a second edge between the same two nodes), so we skip it.
    annotated_pairs = {frozenset((l.start_node, l.related_to_node))
                       for l in graph.links.values() if l.link_tag == 'TLINK'}

    # Comparable timexes, globally ordered by date.
    comparable = sorted(
        ((nid, _date_key(n)) for nid, n in graph.nodes.items()
         if isinstance(n, TimeX.TimeX) and _date_key(n) is not None),
        key=lambda x: x[1])
    if len(comparable) < 2:
        return []

    # Union-find over partitions; each group keeps its constraint list, a taint
    # flag (base-UNSAT member) and a non-factual flag.
    parent = list(range(len(parts)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    g_triples = {i: list(triples[i]) for i in range(len(parts))}
    g_taint = {i: not base_sat[i] for i in range(len(parts))}
    g_nonfactual = {i: (i in nonfactual) for i in range(len(parts))}

    accepted = []
    for (a, ka), (b, kb) in zip(comparable, comparable[1:]):
        rel = _relation(ka, kb)
        if rel == 'CONTAINS':
            continue
        if frozenset((a, b)) in annotated_pairs:
            continue   # an annotated TLINK already relates these timexes
        if rel == 'AFTER':
            a, b, rel = b, a, 'BEFORE'
        pa, pb = part_of.get(a), part_of.get(b)
        if pa is None or pb is None:
            continue
        ga, gb = find(pa), find(pb)
        if ga == gb:
            if g_taint[ga]:
                continue
            if _sat(g_triples[ga] + [(a, rel, b)]):
                g_triples[ga].append((a, rel, b))
                accepted.append((a, rel, b))
        else:
            if g_taint[ga] or g_taint[gb]:
                continue
            # Option (c): never merge a non-factual subordinated group.
            if g_nonfactual[ga] or g_nonfactual[gb]:
                continue
            if _sat(g_triples[ga] + g_triples[gb] + [(a, rel, b)]):
                parent[gb] = ga
                g_triples[ga] = g_triples[ga] + g_triples[gb] + [(a, rel, b)]
                g_nonfactual[ga] = g_nonfactual[ga] or g_nonfactual[gb]
                accepted.append((a, rel, b))

    base_id = max((l.link_id for l in graph.links.values()), default=0)
    links = []
    for i, (a, rel, b) in enumerate(accepted, start=base_id + 1):
        link = Link.Link(i, "TLINK", rel, a, b)
        link._date_inferred = True
        links.append(link)
    return links
