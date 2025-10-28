import os

from pytlex_core.algorithms import Sanity_Check

def try_sco_identity_rule():
    # filepath = r"../pytlex_data/TimeBankCorpus/PRI19980213.2000.0313.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/ea980120.1830.0071.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/WSJ910225-0066.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/APW19980322.0749.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/wsj_0973.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/APW19980301.0720.tml"
    filepath = r"../pytlex_data/TimeBankCorpus/wsj_0158.tml"
    Sanity_Check.sco_identity_rule(filepath)


def try_orphaned_node_rule():
    filepath = r"../pytlex_data/TimeBankCorpus/ABC19980108.1830.0711.tml"
    Sanity_Check.orphaned_node_rule(filepath)


def try_node_to_node_rule():
    filepath = r"../pytlex_data/TimeBankCorpus/PRI19980213.2000.0313.tml"
    Sanity_Check.node_to_node(filepath)


def try_perception_rule():
    filepath = r"../pytlex_data/TimeBankCorpus/ABC19980114.1830.0611.tml"
    Sanity_Check.perception_rule(filepath)


def try_repeating_links_rule():
    filepath = filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
    Sanity_Check.repeating_links(filepath)


def try_conditional_slink_rule():
    # filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/wsj_0158.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/wsj_0924.tml"
    # filepath = r"../pytlex_data/TimeBankCorpus/ABC19980114.1830.0611.tml"
    filepath = r"../pytlex_data/TimeBankCorpus/ABC19980120.1830.0957.tml"

    # filepath = r"../pytlex_data/TimeBankCorpus/AP900815-0044.tml"
    Sanity_Check.conditional_slink_rule(filepath)


def try_ALINK_rule():
    filepath = r"../pytlex_data/TimeBankCorpus/WSJ900813-0157.tml"
    Sanity_Check.ALINK_rule(filepath)


def try_redundant_self_loops_rule():
    filepath = r"../pytlex_data/TimeBankCorpus/AP900816-0139.tml"
    Sanity_Check.redundant_self_loops(filepath)


def try_corpus_sco_identity_rule():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    found_valid = []
    found_missing_identity = []
    total_missing = 0
    total_valid = 0
    total_cases = 0
    for file in corpus_files:
        cases, valid_rule_num, num_missing_identity = Sanity_Check.sco_identity_rule(corpus_path + '/' + file)
        if cases >= 1:
            found_files.append(file)
            total_cases += cases
        if valid_rule_num >= 1:
            found_valid.append(file)
            total_valid += valid_rule_num
        if num_missing_identity >= 1:
            found_missing_identity.append(file)
            total_missing += num_missing_identity

    print("Total Cases: ", total_cases)
    print("Files with SCO Case")
    print(found_files)
    print("# of Files: ", len(found_files))
    print("Files missing Identity link")
    print(found_missing_identity)
    print("Num Missing:", total_missing)

def try_corpus_node_to_node():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    for file in corpus_files:
        result = Sanity_Check.node_to_node(corpus_path + '/' + file)
        if result >= 1:
            print("Found Incorrect File: ", file)
            found_files.append(file)
    print("Incorrect Files")
    print(found_files)
    print("# of Files: ", len(found_files))


def try_corpus_orphaned_node():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    total_orphaned = 0
    total_timex = 0
    for file in corpus_files:
        result = Sanity_Check.orphaned_node_rule(corpus_path + '/' + file)
        if len(result) >= 1:
            print("Found Incorrect File: ", file)
            found_files.append(file)
            total_orphaned += len(result)
            for node in result:
                if "t" in node.get_id_str():
                    total_timex += 1
    print("Incorrect Files")
    print(found_files)
    print("# of Files: ", len(found_files))
    print("# of Orphaned Nodes: ", total_orphaned)
    print("# of Orphaned Timexes: ", total_timex)


def try_corpus_ALINK_rule():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    alink_instances = 0
    alink_violations = 0
    for file in corpus_files:
        valid_alinks, invalid_alinks = Sanity_Check.ALINK_rule(corpus_path + '/' + file)
        alink_instances += valid_alinks
        alink_violations += invalid_alinks
        if invalid_alinks >= 1:
            found_files.append(file)
    print("Incorrect Files")
    print(found_files)
    print("# of Files with Incorrect ALinks: ", len(found_files))
    print("# of Instances of ALINKS: ", alink_instances)
    print("# of ALINK Rule Violations: ", alink_violations)


def try_corpus_perception_rule():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    inc_files = []
    total_cases = 0
    total_violations = 0
    for file in corpus_files:
        valid, violations = Sanity_Check.perception_rule(corpus_path + '/' + file)
        if len(valid) + len(violations) > 0:
            found_files.append(file)
            total_cases += len(valid) + len(violations)
            if len(violations) >= 1:
                total_violations += len(violations)
                inc_files.append(file)
    print("Files with Cases")
    print(found_files)
    print("Files with Violations")
    print(inc_files)
    print("# of Files with Violations: ", len(inc_files))
    print("# of Cases: ", total_cases)
    print("# of Violations: ", total_violations)


def try_corpus_repeating_links():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    total_cases = 0
    for file in corpus_files:
        criminal_links = Sanity_Check.repeating_links(corpus_path + '/' + file)
        if len(criminal_links) >= 1:
            found_files.append(file)
            total_cases += len(criminal_links)
    print("Files with Cases")
    print(found_files)
    print("# of Violations: ", total_cases)


# def try_corpus_conditional_slink():
#     corpus_path = r'../pytlex_data/TimeBankCorpus'
#     corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
#     found_files = []
#     valid_files = []
#     invalid_files = []
#     no_cond_files = []
#     total_cases = 0
#     total_invalid = 0
#     total_no_cond = 0
#     for file in corpus_files:
#         num_ifs, num_no_cond, num_no_ifs = Sanity_Check.conditional_slink_rule(corpus_path + '/' + file)
#
#         if num_ifs >= 1:
#             found_files.append(file)
#             total_cases += num_ifs
#
#         if num_no_ifs >= 1:
#             invalid_files.append(file)
#             total_invalid += num_no_ifs
#         if num_no_cond >= 1:
#             no_cond_files.append(file)
#             total_no_cond += num_no_ifs
#
#     print("\nFiles with Cases")
#     print(found_files)
#     print("# of Cases: ", total_cases)
#     print("Files with slinks and no if clauses: ", invalid_files)
#     print("# of files with no if clauses: ", len(invalid_files))
#     print("# of no if clauses: ", total_invalid)
#
#     print("Files with if clauses and NO conditional SLINKs: ", no_cond_files)
#     print("# of Files with no SLINKs: ", len(no_cond_files))
#     print("# of no slinks: ", total_no_cond)


def try_corpus_conditional_slink():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    valid_files = []
    invalid_files = []
    total_cases = 0
    total_invalid = 0
    total_valid = 0
    for file in corpus_files:
        cases, valid, invalid = Sanity_Check.conditional_slink_rule(corpus_path + '/' + file)

        if len(cases) >= 1:
            found_files.append(file)
            total_cases += len(cases)

            if len(valid) >= 1:
                valid_files.append(file)
                total_valid += len(valid)
            if len(invalid) >= 1:
                invalid_files.append(file)
                total_invalid += len(invalid)
    print("\nFiles with Cases")
    print(found_files)
    print("# of Cases: ", total_cases)
    print("Files with valid if clauses and conditional SLINKs: ", valid_files)
    print("# of Files with valid cases: ", len(valid_files))
    print("# of valid cases: ", total_valid)
    print("Files with if clauses and NO conditional SLINKs: ", invalid_files)
    print("# of files with invalid cases: ", len(invalid_files))
    print("# of invalid cases: ", total_invalid)

def try_corpus_self_loops():
    corpus_path = r'../pytlex_data/TimeBankCorpus'
    corpus_files = [f for _, _, flist in os.walk(corpus_path) for f in flist]
    found_files = []
    total_cases = 0
    for file in corpus_files:
        self_loops = Sanity_Check.redundant_self_loops(corpus_path + '/' + file)
        if len(self_loops) >= 1:
            found_files.append(file)
            total_cases += len(self_loops)
    print("Files with Cases")
    print(found_files)
    print("# of Violations: ", total_cases)


if __name__ == '__main__':
    # try_corpus_sco_identity_rule()
    # try_sco_identity_rule()
    # try_corpus_node_to_node()
    # try_node_to_node_rule()
    # try_corpus_orphaned_node()
    # try_orphaned_node_rule()
    # try_corpus_ALINK_rule()
    # try_ALINK_rule()
    # try_corpus_perception_rule()
    # try_perception_rule()
    # try_corpus_repeating_links()
    # try_repeating_links_rule()
    try_corpus_conditional_slink()
    # try_conditional_slink_rule()
    # try_corpus_self_loops()
    # try_redundant_self_loops_rule()
