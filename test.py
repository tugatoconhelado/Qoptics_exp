from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Qt, Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg

class TestMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        loadUi(
            r'test.ui',
            self
        )



if __name__ == '__main__':
    app = QApplication([])
    w = TestMainWindow()
    w.show()
    app.exec_()