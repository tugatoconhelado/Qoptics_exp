from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.confocal.tracking_widget import TrackingWidget
from qudi.gui.confocal.confocal_widget import ConfocalWidget
from qudi.gui.confocal.position_control_widget import PositionControlWidget
import numpy as np
import pyqtgraph as pg
import sys


class ODMRMainWindow(QMainWindow):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\odmr\newodmr.ui',
            self
        )

if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    main = ODMRMainWindow()
    main.show()
    sys.exit(app.exec_())