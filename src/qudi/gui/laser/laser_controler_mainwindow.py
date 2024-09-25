from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class LaserControllerMainWindow(QMainWindow):

    laser_power_signal = Signal(float)
    laser_frequency_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'laser_controller.ui'),
            self
        )

        self.freqquency_dial_dict = {
            0: 1,
            1: 0,
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
        print('power', power)
        self.laser_power_signal.emit(power)

    def update_power_slider(self):

        value = self.power_spinbox.value()
        power = value / self.power_conversion
        self.power_slider.setValue(power)

    def update_frequency(self, value):

        freq = self.freqquency_dial_dict[value]
        self.frequency_label.setText(f'{freq} Hz')
        self.laser_frequency_signal.emit(freq)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = LaserControllerMainWindow()
    main.show()
    sys.exit(app.exec_())