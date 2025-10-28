import os
from pytlex_core.data import Graph
from pytlex_tests import Testing_utilities

failed = ['ABC19980120.1830.0957.tml', 'AP900815-0044.tml', 'AP900816-0139.tml', 'APW19980213.1380.tml', 'APW19980219.0476.tml', 'APW19980501.0480.tml',
                 'CNN19980126.1600.1104.tml', 'CNN19980213.2130.0155.tml', 'CNN19980227.2130.0067.tml', 'NYT19980206.0460.tml', 'NYT19980206.0466.tml', 'NYT19980402.0453.tml',
                 'PRI19980115.2000.0186.tml', 'PRI19980205.2000.1998.tml', 'PRI19980213.2000.0313.tml', 'PRI19980303.2000.2550.tml', 'PRI19980306.2000.1675.tml',
                 'VOA19980303.1600.2745.tml', 'VOA19980305.1800.2603.tml', 'WSJ900813-0157.tml', 'WSJ910225-0066.tml', 'wsj_0027.tml', 'wsj_0032.tml', 'wsj_0124.tml',
                 'wsj_0132.tml', 'wsj_0135.tml', 'wsj_0144.tml', 'wsj_0158.tml', 'wsj_0159.tml', 'wsj_0168.tml', 'wsj_0169.tml', 'wsj_0171.tml', 'wsj_0175.tml', 'wsj_0184.tml',
                 'wsj_0313.tml', 'wsj_0376.tml', 'wsj_0520.tml', 'wsj_0533.tml', 'wsj_0542.tml', 'wsj_0558.tml', 'wsj_0568.tml', 'wsj_0575.tml', 'wsj_0583.tml', 'wsj_0585.tml',
                 'wsj_0586.tml', 'wsj_0610.tml', 'wsj_0660.tml', 'wsj_0661.tml', 'wsj_0675.tml', 'wsj_0745.tml', 'wsj_0768.tml', 'wsj_0778.tml', 'wsj_0781.tml', 'wsj_0786.tml',
                 'wsj_0786.tml', 'wsj_0791.tml', 'wsj_0798.tml', 'wsj_0810.tml', 'wsj_0816.tml', 'wsj_0918.tml', 'wsj_0927.tml', 'wsj_0938.tml', 'wsj_0950.tml', 'wsj_0973.tml',
                  'wsj_1003.tml', 'wsj_1011.tml', 'wsj_1013.tml', 'wsj_1014.tml']

passed = ['ABC19980108.1830.0711.tml', 'ABC19980114.1830.0611.tml', 'APW19980213.1310.tml', 'APW19980227.0476.tml', 'APW19980227.0494.tml', 'APW19980301.0720.tml', 'APW19980306.1001.tml',
                    'APW19980308.0201.tml', 'APW19980322.0749.tml', 'APW19980418.0210.tml', 'APW19980626.0364.tml', 'CNN19980222.1130.0084.tml', 'CNN19980223.1130.0960.tml', 'ea980120.1830.0071.tml',
                    'ea980120.1830.0456.tml', 'NYT19980212.0019.tml', 'PRI19980121.2000.2591.tml', 'PRI19980205.2000.1890.tml', 'PRI19980216.2000.0170.tml', 'SJMN91-06338157.tml', 'VOA19980303.1600.0917.tml',
                    'VOA19980331.1700.1533.tml', 'VOA19980501.1800.0355.tml', 'wsj_0006.tml', 'wsj_0026.tml', 'wsj_0068.tml', 'wsj_0073.tml', 'wsj_0106.tml', 'wsj_0122.tml', 'wsj_0127.tml', 'wsj_0136.tml',
                    'wsj_0152.tml', 'wsj_0157.tml', 'wsj_0161.tml', 'wsj_0165.tml', 'wsj_0167.tml', 'wsj_0172.tml', 'wsj_0176.tml', 'wsj_0187.tml', 'wsj_0189.tml', 'wsj_0263.tml', 'wsj_0266.tml', 'wsj_0292.tml',
                    'wsj_0316.tml', 'wsj_0321.tml', 'wsj_0324.tml', 'wsj_0329.tml', 'wsj_0332.tml', 'wsj_0340.tml', 'wsj_0344.tml', 'wsj_0346.tml', 'wsj_0348.tml', 'wsj_0356.tml', 'wsj_0471.tml', 'wsj_0505.tml',
                    'APW19980227.0487.tml', 'ed980111.1130.0089.tml', 'NYT19980424.0421.tml', 'wsj_0150.tml', 'wsj_0151.tml', 'wsj_0160.tml', 'wsj_0173.tml', 'wsj_0325.tml', 'wsj_0527.tml',
                    'wsj_0534.tml', 'wsj_0541.tml', 'wsj_0551.tml', 'wsj_0555.tml', 'wsj_0557.tml', 'wsj_0570.tml', 'wsj_0584.tml', 'wsj_0612.tml', 'wsj_0637.tml', 'wsj_0650.tml',
                    'wsj_0662.tml', 'wsj_0667.tml', 'wsj_0670.tml', 'wsj_0674.tml', 'wsj_0679.tml', 'wsj_0685.tml', 'wsj_0695.tml', 'wsj_0706.tml', 'wsj_0709.tml', 'wsj_0713.tml', 'wsj_0736.tml',
                    'wsj_0751.tml', 'wsj_0752.tml', 'wsj_0760.tml', 'wsj_0762.tml', 'wsj_0805.tml', 'wsj_0806.tml', 'wsj_0811.tml', 'wsj_0815.tml', 'wsj_0904.tml', 'wsj_0906.tml', 'wsj_0907.tml',
                    'wsj_0923.tml', 'wsj_0924.tml', 'wsj_0928.tml', 'wsj_0981.tml', 'wsj_0991.tml', 'wsj_1006.tml', 'wsj_1008.tml', 'wsj_1025.tml', 'wsj_1031.tml', 'wsj_1033.tml', 'wsj_1035.tml',
                    'wsj_1038.tml', 'wsj_1039.tml', 'wsj_1040.tml', 'wsj_1042.tml', 'wsj_1073.tml']

def try_run():
    filepath = r"../pytlex_data/TimeBankCorpus"
    i = 0
    for _, _, files in os.walk(filepath):
        for filename in files:
            graph = Graph(filepath=filepath + "/" + filename)
            print("{}\t{}".format(filename, graph.consistency))
            if graph.consistency:
                i += 1

    print(i)


def try_wsj_0006():
    filepath = r"../pytlex_data/TimeBankCorpus/wsj_0026.tml"
    graph = Graph.Graph(filepath=filepath)

    for partition in graph.main_graphs:
        for node in partition.nodes:
            print(node.get_id_str())

    print("\n\n\n")

    for partition in graph.subordination_graphs:
        for node in partition.nodes:
            print(node.get_id_str())
        print("\n")

    print("\n\n\n")


    print("First Point: {}".format(graph.get_first_point()))
    print("Last Point: {}".format(graph.get_last_point()))
    print("Total Time Points: {}".format(graph.get_total_time_points()))
    print("Main timeline length: {}".format(graph.get_timeline_length()))
    print("Main Timeline: {}".format(graph.timeline))
    print("Subordinate Timelines: ")
    for timeline in graph.subordinate_timelines():
        print(timeline)

    print("\nAttachment points: ")
    for a_p in graph.get_attachement_points():
        print(a_p)

    print("Indeterminacy Score: {}".format(graph.indeterminacy_score))

    print(graph.get_suggested_links())

def try_wsj_0918():
    filepath = r"../pytlex_data/TimeBankCorpus/wsj_0918.tml"
    graph = Graph.Graph(filepath=filepath)

    for partition in graph.main_graphs:
        for node in partition.nodes:
            print(node.get_id_str())

    print("\n\n\n")

    for partition in graph.subordination_graphs:
        for node in partition.nodes:
            print(node.get_id_str())
        print("\n")

    print("\n\n\n")


    print("First Point: {}".format(graph.get_first_point()))
    print("Last Point: {}".format(graph.get_last_point()))
    print("Total Time Points: {}".format(graph.get_total_time_points()))
    print("Main timeline length: {}".format(graph.get_timeline_length()))
    print("Main Timeline: {}".format(graph.timeline))
    print("Subordinate Timelines: ")
    for timeline in graph.subordinate_timelines():
        print(timeline)

    print("\nAttachment points: ")
    for a_p in graph.get_attachement_points():
        print(a_p)

    print("Indeterminacy Score: {}".format(graph.indeterminacy_score))

    print(graph.get_suggested_links())

def try_all_indeterminacies():
    filepath = r"../pytlex_data/TimeBankCorpus/"
    for _, _, files in os.walk(filepath):
        for filename in files:
            graph = Graph.Graph(filepath=filepath + "/" + filename, apply_suggested_links=True)
            print("{}\t{}\t{}".format(filename, graph.indeterminacy_score, graph.consistency))

def try_one_indeterminacy(filename):
    filepath = r"../pytlex_data/TimeBankCorpus/" + filename
    graph = Graph.Graph(filepath=filepath)
    print("{}\t{}".format(filename, graph.indeterminacy_score))


def output():
    filepath = r"../pytlex_data/TimeBankCorpus"
    for subdir, dirs, files in os.walk(filepath):
        for filename in files:
            graph = Graph.Graph(filepath=filepath + "/" + filename)
            print(len(graph.nodes), end="\t")

            if filename not in Testing_utilities.failed_parse:
                largest_partition = 0
                for partition in graph.main_graphs + graph.subordination_graphs:
                    if len(partition.links) > largest_partition:
                        largest_partition = len(partition.links)

                print(largest_partition, end="")
            print()


def try_json():
    filename = r"../pytlex_data/TimeBankCorpus/wsj_0026.tml"
    graph = Graph.Graph(filepath=filename)

    print(graph.to_json())

def check_4_files():
    path = r"../pytlex_data/TimeBankCorpus/"
    problematic_bunch = {'ABC19980304.1830.1636.tml', 'APW19980213.1320.tml', 'APW19980227.0468.tml', 'APW19980227.0489.tml'}

    for filename in problematic_bunch:
        print("-------------------------------------")
        print(filename)
        graph = Graph.Graph(filepath=path + filename)


if __name__ == '__main__':
    try_wsj_0918()
