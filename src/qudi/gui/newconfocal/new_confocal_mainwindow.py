from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.newconfocal.tracking_widget import TrackingWidget
from qudi.gui.newconfocal.confocal_widget import ConfocalWidget
from qudi.gui.newconfocal.position_control_widget import PositionControlWidget
import numpy as np
import pyqtgraph as pg
import sys
import os


class ConfocalMainWindow(QMainWindow):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'newconfocal.ui'),
            self
        )
        self.setStyleSheet(open('/Users/nicky/Scripts/Qoptics_exp/artwork/styles/dark_purple.qss').read())

        self.tracking_widget = TrackingWidget(self)
        self.tracking_dockwidget.setWidget(self.tracking_widget)

        self.confocal_widget = ConfocalWidget(self)
        self.confocal_dockwidget.setWidget(self.confocal_widget)

        self.position_control_widget = PositionControlWidget(self)
        self.position_control_dockwidget.setWidget(self.position_control_widget)

        #self.exit_action.triggered.connect(self.close, Qt.QueuedConnection)

        #self.progress_bar_timer = QTimer()
        #self.progress_bar_timer.setInterval(5000)
        #self.progress_bar_timer.timeout.connect(self.hide_progress_bar)

        #self.set_status_bar()

    def set_status_bar(self):

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setAlignment(Qt.AlignRight)
        self.progress_bar.setFixedSize(100, 15)
        self.statusbar.addPermanentWidget(self.progress_bar)
        self.setStatusBar(self.statusbar)

        self.hide_progress_bar()

    @Slot(int, int)
    def update_status_bar_progress(self, value: int, timeout=5000) -> None:

        if value == 0:
            self.progress_bar.show()
            self.progress_bar_timer.stop()
        self.progress_bar.setValue(value)

        if value == 100:
            self.progress_bar_timer.start()

    def hide_progress_bar(self):

        self.progress_bar.hide()
        self.progress_bar_timer.stop()


if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    w = ConfocalMainWindow()
    w.show()
    w.raise_()
    sys.exit(app.exec_())