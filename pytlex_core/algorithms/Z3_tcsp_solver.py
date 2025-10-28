from z3 import *

from pytlex_tests import Testing_utilities


def solve(graph):
    s = Solver()

    for node in graph.nodes.values():
        node_minus = Int(node.get_id_str() + "_minus")
        node_plus = Int(node.get_id_str() + "_plus")
        s.add(node_minus < node_plus)
        s.add(node_minus > 0)

    for link in graph.links.values():
        a_minus = Int(link.start_node + "_minus")
        a_plus = Int(link.start_node + "_plus")
        b_minus = Int(link.related_to_node + "_minus")
        b_plus = Int(link.related_to_node + "_plus")

        if link.rel_type == "AFTER":
            s.add(b_plus < a_minus)
        elif link.rel_type == "BEFORE":
            s.add(a_plus < b_minus)
        elif link.rel_type == "IBEFORE":
            s.add(a_plus == b_minus)
        elif link.rel_type == "IAFTER":
            s.add(b_plus == a_minus)
        elif link.rel_type in {"BEGINS", "INITIATES"}:
            s.add(a_minus == b_minus)
            s.add(a_plus < b_plus)
        elif link.rel_type == "BEGUN_BY":
            s.add(a_minus == b_minus)
            s.add(b_plus < a_plus)
        elif link.rel_type in {"ENDS", "CULMINATES", "TERMINATES"}:
            s.add(b_minus < a_minus)
            s.add(a_plus == b_plus)
        elif link.rel_type == "ENDED_BY":
            s.add(a_minus < b_minus)
            s.add(a_plus == b_plus)
        elif link.rel_type == "INCLUDES":
            s.add(a_minus < b_minus)
            s.add(b_plus < a_plus)
        elif link.rel_type in {"IS_INCLUDED", "CONTINUES", "REINITIATES"}:
            s.add(b_minus < a_minus)
            s.add(a_plus < b_plus)
        elif link.rel_type in {"SIMULTANEOUS", "IDENTITY", "DURING", "DURING_INV"}:
            s.add(a_minus == b_minus)
            s.add(a_plus == b_plus)

    if s.check().r == Z3_L_TRUE:
        m = s.model()
        solution = {}
        for d in m.decls():
            if str(m[d]) in solution.keys():
                solution[str(m[d])].append(str(d))
            else:
                solution[str(m[d])] = []
                solution[str(m[d])].append(str(d))
        return sort(solution)
    else:
        return None


def sort(s):
    ret = {}
    for key in sorted(s):
        ret[key] = s[key]
    return ret


if __name__ == '__main__':
    g = Testing_utilities.consistent_graph_1()

    solve(g)
