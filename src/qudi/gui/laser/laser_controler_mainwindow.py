from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class LaserControllerMainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'laser_controller.ui'),
            self
        )   
        self.setStyleSheet(open('/Users/nicky/Scripts/Qoptics_exp/artwork/styles/dark_purple.qss').read())

        self.bh_laser_widget = BHLaserWidget()
        self.bh_laser_dockwidget.setWidget(self.bh_laser_widget)

        self.thorlabs_laser_widget = ThorlabsLaserWidget()
        self.thorlabs_laser_dockwidget.setWidget(self.thorlabs_laser_widget)

        self.laser_combobox.currentIndexChanged.connect(self._on_laser_changed)

        self.configure_plots()

    def _on_laser_changed(self, index):

        if index == 0:
            self.saturation_plot.setLabel('bottom', 'Power', units='V')
        elif index == 1:
            self.saturation_plot.setLabel('bottom', 'Power', units='mA')

    def configure_plots(self):

        self.saturation_dataline = self.saturation_plot.plot([1,2,3,4], [1,4,9,16], pen='yellow')
        self.saturation_plot.setLabel('left', 'Intensity', units='cts/sec')
        self.saturation_plot.setLabel('bottom', 'Power', units='V')

class ThorlabsLaserWidget(QWidget):

    laser_power_signal = Signal(float)
    laser_frequency_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'thorlabs_laser_widget.ui'),
            self
        )

        self.power_conversion = 200 / 1000 # mA / steps
        self.editing_status = False

        self.init_setup()

    def init_setup(self):

        self.power_dial.valueChanged.connect(self.update_power_spinbox)
        self.power_spinbox.lineEdit().returnPressed.connect(self.update_power_dial)

    @Slot()
    def update_power_spinbox(self):

        value = self.power_dial.value()
        power = value * self.power_conversion
        self.power_spinbox.setValue(power)
        self.laser_power_signal.emit(power)

    @Slot()
    def update_power_dial(self):

        value = self.power_spinbox.value()
        power = value / self.power_conversion
        self.power_dial.setValue(power)  

    @Slot(float)
    def update_power_status(self, value: float):

        power = value / self.power_conversion
        self.power_dial.setValue(power)
        self.power_spinbox.setValue(value)

class BHLaserWidget(QWidget):

    laser_power_signal = Signal(float)
    laser_frequency_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'bh_laser_widget.ui'),
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
        self.editing_status = False

        self.init_setup()

    def init_setup(self):

        self.power_dial.valueChanged.connect(self.update_power_spinbox)
        self.frequency_dial.valueChanged.connect(self.update_frequency)
        self.power_spinbox.lineEdit().returnPressed.connect(self.update_power_dial)

        self.update_frequency(0)

    @Slot()
    def update_power_spinbox(self):

        value = self.power_dial.value()
        power = value * self.power_conversion
        self.power_spinbox.setValue(power)
        self.laser_power_signal.emit(power)

    @Slot()
    def update_power_dial(self):

        value = self.power_spinbox.value()
        power = value / self.power_conversion
        self.power_dial.setValue(power)

    @Slot()
    def update_frequency(self, value):

        freq = self.freqquency_dial_dict[value]
        self.frequency_label.setText(f'Frequency: {freq} MHz')
        if freq == 1:
            self.frequency_label.setText(f'Frequency: Off')
        elif freq == 0:
            self.frequency_label.setText(f'Frequency: CW')
        self.laser_frequency_signal.emit(freq)

    @Slot(int)
    def update_frequency_status(self, value):

        self.editing_status = True
        self.frequency_label.setText(f'Frequency: {value} Hz')
        for key, freq_value in self.freqquency_dial_dict.items():
            if freq_value == value:
                self.frequency_dial.setValue(value)
        self.editing_status = False

    @Slot(float)
    def update_power_status(self, value):

        power = value / self.power_conversion
        self.power_dial.setValue(power)
        self.power_spinbox.setValue(value)

if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    main = LaserControllerMainWindow()
    main.show()
    sys.exit(app.exec_())