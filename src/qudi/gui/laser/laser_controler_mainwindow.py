from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys


class LaserControllerMainWindow(QMainWindow):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\laser\laser_controller.ui',
            self
        )

        self.freqquency_dial_dict = {
            0: 0,
            1: 1,
            2: 20, 
            3: 50,
            4: 80
        }

        self.power_conversion = 10 / 1000 # V / steps

        self.init_setup()

    def init_setup(self):


        self.power_slider.valueChanged.connect(self.update_power_spinbox)
        self.frequency_dial.valueChanged.connect(self.update_frequency)
        self.power_spinbox.lineEdit().returnPressed.connect(self.update_power_slider)


    def update_power_spinbox(self):

        value = self.power_slider.value()
        power = value * self.power_conversion
        self.power_spinbox.setValue(power)

    def update_power_slider(self):

        value = self.power_spinbox.value()
        power = value / self.power_conversion
        self.power_slider.setValue(power)

    def update_frequency(self, value):

        freq = self.freqquency_dial_dict[value]
        self.frequency_label.setText(f'{freq} Hz')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = LaserControllerMainWindow()
    main.show()
    sys.exit(app.exec_())