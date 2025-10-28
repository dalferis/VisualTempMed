import os
import time
from pytlex_core import Sanity_Check, Graph, Inconsistency_detector


def timebank_evaluation():
    """
    This method evaluates the Timebank Corpus for several errors, including:
    - The Subject + Causative Object - Identity Rule (SCO) aka Causative Event Rule
    - The Evidential Link Rule/Perception Event Rule
    - The Conditional Link Rule
    - The ALINK Replacement Rule
    - The ALINK-SLINK Incompatability Rule
    - Inconsistent Subgraphs
    - Disconnected Graphs
    - Redundant Self-Loops
    """
    filepath = r"../pytlex_data/TimeBankCorpus/"
    sco_total_instances = 0
    sco_total_violations = 0

    evidential_total_instances = 0
    evidential_total_violations = 0

    conditional_total_instances = 0
    conditional_total_violations = 0

    alink_total_instances = 0
    alink_total_violations = 0

    inconsistent_subgraphs_instances = 0

    alink_slink_total_violations = 0

    disconnectivity_instances = 0
    disconnectivity_total_links = 0

    self_loop_instances = 0
    self_loop_count = 0

    for _, _, files in os.walk(filepath):
        for filename in files:
            """ 
            Checking for Evidential/Perception Rule Violations
            """
            evidential_instances, evidential_violations = Sanity_Check.perception_rule(filepath + "/" + filename)
            evidential_total_instances += evidential_instances
            evidential_total_violations += evidential_violations

            """ 
            Checking for Conditional Rule Violations
            """
            if_instances, conditional_violations = Sanity_Check.conditional_slink_rule(
                filepath + "/" + filename)
            conditional_total_instances += if_instances
            conditional_total_violations += conditional_violations

            """ 
            Checking for Subject + Causative - Identity Rule (Causative Event Rule) Violations
            """
            sco_instances, sco_violations = Sanity_Check.sco_identity_rule(filepath + "/" + filename)
            sco_total_instances += sco_instances
            sco_total_violations += sco_violations

            """ 
            Checking for ALINK Replacement Violations
            """
            alink_instances, alink_violations = Sanity_Check.ALINK_rule(filepath + "/" + filename)
            alink_total_instances += alink_instances
            alink_total_violations += alink_violations

            alink_slink_violations = Sanity_Check.node_to_node(filepath + "/" + filename)
            alink_slink_total_violations += alink_slink_violations

            """ 
            Checking for all Inconsistent Subgraphs Instances
            """
            graph = Graph.Graph(filepath=filepath + "/" + filename)
            if graph.consistency is False:
                inconsistent_subgraphs_instances += 1

            """ 
            Checking for Disconnected Graphs
            """
            if graph.get_suggested_links() is not None and len(graph.get_suggested_links()) > 0:
                disconnectivity_instances += 1
                disconnectivity_total_links += len(graph.get_suggested_links())

            """ 
            Checking for Redundant Self-Loops
            """
            self_loops = Sanity_Check.redundant_self_loops(filepath + "/" + filename)
            if len(self_loops) > 0:
                self_loop_instances += 1
                self_loop_count += len(self_loops)

    """ 
    Printing Out Results
    """
    print("Perception/Evidential Rule Instances:\t", evidential_total_instances,
          "\t Perception/Evidential Rule Violations:", evidential_total_violations)

    print("Conditional Rule Instances:\t", conditional_total_instances,
          "\t Conditional Rule Violations:", conditional_total_violations)

    print("Subject + Causative - IDENTITY Rule Instances:\t", sco_total_instances,
          "\t Subject + Causative - IDENTITY Rule Violations:",
          sco_total_violations)

    print("ALINK Replacement Rule Instances:\t", alink_total_instances,
          "\t ALINK Replacement Rule Violations:", alink_total_violations)

    print("ALINK-SLINK Incompatibility Rule:\t", alink_slink_total_violations)

    print("Inconsistent Graphs (File Count):\t", inconsistent_subgraphs_instances)

    print("Disconnectivity Instances (File Count):\t", disconnectivity_instances, "\t Disconnectivity Violations:\t",
          disconnectivity_total_links)

    print("Redundant Self-Loops Instances:\t", self_loop_instances, "\t Redundant Self-Loops Violations:\t",
          self_loop_count)


if __name__ == '__main__':
    start_time = time.time()
    timebank_evaluation()
    print("Evaluation took", time.time() - start_time, "seconds to run")
