from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class PulsedESRMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'pulsed_esr2.ui'),
            self
        )


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = PulsedESRMainWindow()
    widget.show()
    sys.exit(app.exec_())