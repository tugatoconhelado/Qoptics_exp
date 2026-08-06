# -*- coding: utf-8 -*-

__all__ = ["TimeTraceGui"]

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox, QTableWidgetItem
from PySide2.QtCore import Slot, Qt, Signal

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.pulsed_exp.sequence_editor.structures import Sequence
from qudi.gui.pulsed_exp.pulsed_exp_mainwindow import PulsedExpMainWindow
import functools
import pyqtgraph as pg


class PulsedExpGui(GuiBase):
    """This is a simple template GUI measurement module for qudi"""

    add_channel_to_logic_signal = Signal(int, list, str, int)
    prepare_frame_signal = Signal(int)
    add_pulse_to_logic_signal = Signal(float, float, str, str, list, int)
    run_exp_signal = Signal(Sequence, int, int, dict)
    stop_exp_signal = Signal()
    frame_to_logic_signal = Signal(int)
    simulation_to_logic = Signal(int, int, int)
    clear_channels_signal = Signal()

    _pulsed_exp_logic = Connector(name="pulsed_exp_logic", interface="PulsedExpLogic")

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self._mw = PulsedExpMainWindow()  # initializes the UI form


        ####### RUn Experiment #######
        # from gui window to gui slots
        self._mw.run_sequence_button.clicked.connect(self.run_experiment)
        self._mw.stop_sequence_button.clicked.connect(self.stop_experiment)
        # from gui slots to logic
        self.run_exp_signal.connect(
            self._pulsed_exp_logic().run_experiment, Qt.QueuedConnection)
        self.stop_exp_signal.connect(
            self._pulsed_exp_logic().stop_experiment, Qt.QueuedConnection)

        ###### Switch outputs #######
        self._mw.pb_output_status_signal.connect(
            self._pulsed_exp_logic().switch_pb_outputs,
            Qt.QueuedConnection,
        )
        self._mw.pb_output_stop_signal.connect(
            self._pulsed_exp_logic().stop_pb_outputs,
            Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            self._pulsed_exp_logic().save_data,
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            self._pulsed_exp_logic().load_data,
            Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            self._pulsed_exp_logic().load_next_data,
            Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            self._pulsed_exp_logic().load_previous_data,
            Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            self._pulsed_exp_logic().delete_file,
            Qt.QueuedConnection
        )

        self._pulsed_exp_logic().data_signal.connect(
            self._mw.update_pulsed_exp_plot,
            Qt.QueuedConnection
        )
        self._pulsed_exp_logic().status_msg.connect(
            self._mw.update_status_bar,
            Qt.QueuedConnection
        )

        self._pulsed_exp_logic().file_changed_signal.connect(
            self._mw.update_filename
        )

        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        # self._template_logic().sigCounterupdate_buttond.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    @property
    def sequence(self):
        return self._mw.sequence_editor.sequence

    @Slot()
    def run_experiment(self):

        x_loop = self._mw.loop_sequence_spinbox.value()
        repeat_exp = self._mw.repeat_exp_spinbox.value()

        track = self._mw.track_checkbox.isChecked()
        interval = self._mw.track_every_spinbox.value()
        track_options = {
            'track': track,
            'interval': interval
        }
        self.run_exp_signal.emit(self.sequence, x_loop, repeat_exp, track_options)
        self._mw.filename_label.setText("")

    @Slot()
    def stop_experiment(self):
        # self._pulsed_exp_logic().Stop_Experiment()
        self.stop_exp_signal.emit()

    @Slot(str)
    def show_error_message(self, error_str):
        """
        This function is called when an error occurs.
        It shows an error message to the user.
        """
        dlg = QMessageBox(self._mw)
        dlg.setWindowTitle("Error!")
        dlg.setText(error_str)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def show(self) -> None:
        """Show the main window and raise it above all others"""
        self._mw.show()
        self._mw.raise_()
