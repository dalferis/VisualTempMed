import sys
from dataModel import DataModel
import mainWindow as mw
from pytlex_core.data import Graph
from pytlex_core.algorithms import TLEX
from PySide6.QtWidgets import QApplication

def visualize(filepath):
    graph = Graph.Graph(filepath=filepath)
    tlex = TLEX.TLEX(graph=graph)
    model = DataModel(graph, tlex)
    app = QApplication(sys.argv)
    window = mw.MainWindow(model)
    window.show()
    sys.exit(app.exec())
