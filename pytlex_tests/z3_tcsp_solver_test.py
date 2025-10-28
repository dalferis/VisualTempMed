from pytlex_core.algorithms import Z3_tcsp_solver
from pytlex_core.data import Graph


# Methods to test:
# solve() - sort()

class Z3_Tester:

    tester_graph = Graph.Graph(None, None, r"../pytlex_data/TimeBankCorpus/wsj_0026.tml", None)

    def test_solve(self):
        print(Z3_tcsp_solver.solve(self.tester_graph))


if __name__ == "__main__":
    temp = Z3_Tester()
    temp.test_solve()

