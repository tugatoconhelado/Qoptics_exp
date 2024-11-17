# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt, Signal

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.polarization.polarization_mainwindow import PolarizationMainWindow
from qudi.logic import filemanager
from qudi.logic import plot
import functools


class PolarizationGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    move_to_angle_signal = Signal(float)
    move_polarizer_by_step_signal = Signal(int, int)
    start_polarization_experiment_signal = Signal(int, int, int, float, float, str)

    _polarization_logic = Connector(name='polarization_logic', interface='PolarizationLogic')
    _polarizer_motor_hardware = Connector(name='polarizer_motor_hardware', interface='PolarizerMotorHardware')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        # initialize the main window
        self._mw = PolarizationMainWindow()

        # connect all GUI internal signals
        self._mw.refresh_button.clicked.connect(self.update_motor_device_list)
        self._mw.connect_button.clicked.connect(self.initialise_motor)
        self._mw.up_button.clicked.connect(self.move_up)
        self._mw.down_button.clicked.connect(self.move_down)
        self._mw.move_button.clicked.connect(self.move_to_angle)
        self._mw.start_button.clicked.connect(self.start_polarization_experiment)


        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self._polarization_logic().polarizer_angle_signal.connect(
            self.update_position,
            QtCore.Qt.QueuedConnection
        )
        self.move_to_angle_signal.connect(
            self._polarization_logic().move_polarizer_to_angle,
            QtCore.Qt.QueuedConnection
        )
        self.move_polarizer_by_step_signal.connect(
            self._polarization_logic().move_polarizer_by_steps,
            QtCore.Qt.QueuedConnection
        )
        self.start_polarization_experiment_signal.connect(
            self._polarization_logic().start_rotation_experiment,
            QtCore.Qt.QueuedConnection
        )

        self._polarization_logic().data_signal.connect(
            self._mw.update_plot,
            QtCore.Qt.QueuedConnection
        )
        self._mw.stop_button.clicked.connect(
            self._polarization_logic().stop_acquisition,
            QtCore.Qt.QueuedConnection
        )
        self._polarizer_motor_hardware().position_signal.connect(
            self.update_position,
            QtCore.Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            self._polarization_logic().save_data,
            QtCore.Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            self._polarization_logic().load_data,
            QtCore.Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            self._polarization_logic().delete_file,
            QtCore.Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            self._polarization_logic().load_next_data,
            QtCore.Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            self._polarization_logic().load_previous_data,
            QtCore.Qt.QueuedConnection
        )

        self._polarization_logic().file_changed_signal.connect(
            self.change_current_file_labels,
            QtCore.Qt.QueuedConnection
        )

        self._mw.previous_button.clicked.emit()
        # Show the main window and raise it above all others

        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    @Slot()
    def start_polarization_experiment(self):
        
        steps = self._mw.no_of_steps_spinbox.value()
        time_per_point = self._mw.time_per_point_spinbox.value()
        samp_freq = self._mw.samp_freq_spinbox.value()
        start = self._mw.start_angle_spinbox.value()
        angle_range = self._mw.range_angle_spinbox.value()
        input_device = self._mw.input_combobox.currentText()

        self.start_polarization_experiment_signal.emit(
            steps,
            time_per_point,
            samp_freq,
            start,
            angle_range,
            input_device
        )

    @Slot()
    def update_motor_device_list(self):
        self._mw.devices_combobox.clear()
        devices = self._polarizer_motor_hardware().get_device_list()
        for device in devices:
            self._mw.devices_combobox.addItem(device[0] + '|' + device[1])

    def initialise_motor(self):

        device = self._mw.devices_combobox.currentText().split('|')
        if device == ['']:
            return
        self._polarizer_motor_hardware().initialise_motor(device[0])
        self._mw.current_position_label.setText(
            str(self._polarizer_motor_hardware().get_position())
        )

    @Slot()
    def move_to_angle(self):

        position = self._mw.position_spinbox.value()
        self.move_to_angle_signal.emit(position)

    @Slot()
    def move_up(self):
        steps = self._mw.polarizer_steps_spinbox.value()
        self.move_polarizer_by_step_signal.emit(1, steps)

    @Slot()
    def move_down(self):
        steps = self._mw.polarizer_steps_spinbox.value()
        self.move_polarizer_by_step_signal.emit(-1, steps)

    @Slot(float)
    def update_position(self, position: float) -> None:
        self._mw.current_position_label.setText(
            str(round(position,2))
        )

    @Slot(str)
    def change_current_file_labels(self, filepath: str) -> None:

        head, filename = os.path.split(filepath)
        self._mw.linear_plot_widget.setTitle(filename, **{'size': '7pt'})
        self._mw.filename_label.setText(filename)

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
