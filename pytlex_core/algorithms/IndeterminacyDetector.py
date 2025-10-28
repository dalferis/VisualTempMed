from z3 import *
from pytlex_core.algorithms import Z3_tcsp_solver
from pytlex_core.data import Graph


# Algorithm to solve the score, indeterminant_time_points, indeterminant_sections, indeterminant_time_pairs
# on a GraphML object that is not None or empty
from pytlex_core.timeline.Indeterminacy import Indeterminacy


def solve(graph: Graph):
    if graph is None:
        raise Exception("Graph cannot be 'None' or empty")
    if len(graph.links) == 0:
        return Indeterminacy(None, None, None, None, None, None)
    shortest_solution = Z3_tcsp_solver.solve(graph)

    if shortest_solution is None:
        return Indeterminacy(None, None, None, None, None, None)

    set_option('smt.arith.random_initial_value', True)
    random_timelines = []
    for x in range(100):  # Creates 100 randomized timelines
        random_timeline = Z3_tcsp_solver.solve(graph)
        if random_timeline is not None:
            r_timeline = {int(k): val for k, val in random_timeline.items()}
            timeline = {}
            for key, value in sorted(r_timeline.items()):
                timeline[key] = value
            random_timelines.append(timeline)

    set_option('smt.arith.random_initial_value', False)
    indeterminant_sections = set()
    indeterminant_time_points = set()
    total = 0
    for key in shortest_solution.keys():
        total += len(shortest_solution[key])
    indeterminant_time_pairs = [False] * (total - 1)
    indeterminant_indexes = []

    left = 0
    right = 1
    shortest_timeline = sum(shortest_solution.values(), [])  # Converts timeline into a list

    while right < len(indeterminant_time_pairs):  # Checks every adjacent timepoint pair
        left_hand_side = shortest_timeline[left]
        right_hand_side = shortest_timeline[right]

        for random_timeline in random_timelines:  # Checks in each timeline for each pair
            timeline = sum(random_timeline.values(), [])

            if (timeline.index(left_hand_side) >= timeline.index(right_hand_side)) or \
                    (timeline.index(right_hand_side) - timeline.index(left_hand_side) != 1):
                indeterminant_indexes.append(right)
                indeterminant_time_pairs[left] = True  # If right point appears before left or if it is not adjacent
                break

        left += 1
        right += 1
    score = sum(indeterminant_time_pairs) / len(indeterminant_time_pairs)

    return Indeterminacy(shortest_solution, score, indeterminant_time_points, indeterminant_sections, indeterminant_time_pairs, indeterminant_indexes)


# find total timepoints in a timeline
def total_time_points(timeline: dict[str, list[str]]) -> int:
    sum = 0
    for section in timeline.items():
        sum += len(section[1])
    return sum


# find a link between nodes
def link_between(node1, node2, graph) -> bool:
    for link in graph.links.values():
        if type(node1) is str:
            if (graph.nodes[link.start_node].get_id_str() == node1 and graph.nodes[
                link.related_to_node].get_id_str() == node2) or \
                    (graph.nodes[link.start_node].get_id_str() == node2 and graph.nodes[
                        link.related_to_node].get_id_str() == node1):
                return True
        else:
            if (graph.nodes[link.start_node] is node1 and graph.nodes[link.related_to_node] is node2) or \
                    (graph.nodes[link.start_node] is node2 and graph.nodes[link.related_to_node] is node1):
                return True
    return False


def solve_with_new_constraint(graph: Graph, equal: bool, time_point1: str, time_point2: str):
    if graph is None or time_point1 == "" or time_point2 == "":
        raise Exception("Graph cannot be 'None or have empty starting points.'")

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

    tp1 = Int(str(time_point1))
    tp2 = Int(str(time_point2))

    if equal:
        s.add(tp1 == tp2)
    else:
        s.add(tp1 != tp2)

    return s.check().r == Z3_L_TRUE
