from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import sys
import os


class ImplanterMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'Implanter.ui'),
            self
        )
       

if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    w = ImplanterMainWindow()
    w.show()
    w.raise_()
    sys.exit(app.exec_())