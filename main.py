import argparse
import sys
from pytlex_core.data import Event, Graph, Instance, TimeX, Signal, Link
from pytlex_core.algorithms import TLEX

def main():
    parser = argparse.ArgumentParser(description='Visual Temporal Medical')
    parser.add_argument('--inputfile', '-i', nargs=1, required=True, help='Input file for analyse')
    try:
        args = parser.parse_args()
    except SystemExit as e:
        return
    
    # Example 1
    # event1 = Event.Event(1, "REPORTING", "Test Stem")
    # node2 = Instance.Instance(2, "event1", event1, "PAST", "NONE", "NOUN", "POS")
    # node3 = TimeX.TimeX(3, "Test Value", True, "Test Phrase")
    # link1 = Link.Link(1, "ALINK", "INITIATES", node2.get_id_str(), node3.get_id_str())
    # node_set = {node2 , node3}
    # link_set = {link1}
    # graph = Graph.Graph(nodes = node_set, links = link_set)

    # Example 2
    graph = Graph.Graph(filepath = args.inputfile[0])
    tlex = TLEX.TLEX(graph = graph)
    print(tlex.partitions)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")