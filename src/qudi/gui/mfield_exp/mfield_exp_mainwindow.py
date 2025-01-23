from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir, Qt
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os
import serial


class MFieldExpMainWindow(QMainWindow):

    move_signal = Signal(int, str)
    start_mag_field_exp_signal = Signal(int, int, int)
    connect_signal = Signal(str)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'magnetic_field_exp.ui'),
            self
        )
        self.move_button.clicked.connect(self.move_by_steps, Qt.QueuedConnection)
        self.go_to_button.clicked.connect(self.go_to_position, Qt.QueuedConnection)
        self.start_button.clicked.connect(self.start_mag_field_exp, Qt.QueuedConnection)
        self.connect_button.clicked.connect(self.connect_to_port, Qt.QueuedConnection)

        self.configure_plots()

    def move_by_steps(self):
        steps = self.no_of_steps_spinbox.value()
        direction = self.direction_combobox.currentText()
        self.move_signal.emit(steps, direction)

    def go_to_position(self):

        position = self.move_to_spinbox.value()
        self.move_signal.emit(position, "Absolute")

    def start_mag_field_exp(self):
        print('Starting magnetic field experiment')
        self.filename_label.setText("")
        self.plot_widget.setTitle("")
        range = self.scan_range_spinbox.value()
        steps = self.scan_steps_spinbox.value()
        track_every = self.track_every_spinbox.value()
        self.start_mag_field_exp_signal.emit(range, steps, track_every)

    def configure_plots(self):

        self.plot_widget.setBackground('black')
        self.plot_widget.setLabel('left', 'Intensity (cps)')
        self.plot_widget.setLabel('bottom', 'Magnetic Field (steps)')

        self.dataline = self.plot_widget.plot([], [], pen='yellow')

    @Slot(np.ndarray, np.ndarray)
    def update_plot(self, mag_field, counts):
        self.dataline.setData(mag_field, counts)

    def update_position(self, position):
        self.current_position_label.setText(str(position))


    def connect_to_port(self):
        port = self.com_ports_combobox.currentText()
        port = port.split(':')[0]
        self.connect_signal.emit(port)

    @Slot(list)
    def update_com_ports_list(self, ports):
        self.com_ports_combobox.clear()
        for port, desc, hwid in ports:
            port_str = port + ': ' + desc
            self.com_ports_combobox.addItem(port_str)

    

if __name__ == "__main__":
    # Check if a QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    hud = MFieldExpMainWindow()
    hud.show()

    sys.exit(app.exec_())