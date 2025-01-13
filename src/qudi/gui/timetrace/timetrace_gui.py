# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.timetrace.timetrace_mainwindow import TimeTraceMainWindow
from qudi.logic import filemanager
from qudi.logic import plot
import functools


class TimeTraceGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _timetrace_logic = Connector(name='timetrace_logic', interface='TimeTraceLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        # initialize the main window
        self._mw = TimeTraceMainWindow()

        # connect all GUI internal signals

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self._mw.start_experiment_signal.connect(
            self._timetrace_logic().start_acquisition,
            Qt.QueuedConnection
        )
        self._timetrace_logic().data_signal.connect(
            self._mw.update_plot,
            Qt.QueuedConnection
        )
        self._mw.stop_button.clicked.connect(
            self._timetrace_logic().stop_acquisition,
            Qt.QueuedConnection
        )
        self._mw.export_action.triggered.connect(
            self.export_plot,
            Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            functools.partial(
                self._timetrace_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_action.triggered.connect(
            functools.partial(
                self._timetrace_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            functools.partial(
                self._timetrace_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_action.triggered.connect(
            functools.partial(
                self._timetrace_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_as_action.triggered.connect(
            functools.partial(
                self._timetrace_logic().save_data_as
            ),
            Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            functools.partial(
                self._timetrace_logic().load_previous_data
            ),
            Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            functools.partial(
                self._timetrace_logic().load_next_data
            ),
            Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            functools.partial(
                self._timetrace_logic().delete_file
            ),
            Qt.QueuedConnection
        )

        self._timetrace_logic().file_changed_signal.connect(
            self.change_current_file_labels,
            Qt.QueuedConnection
        )
        self._timetrace_logic().status_msg_signal.connect(
            self.update_statusbar,
            Qt.QueuedConnection
        )
        self._timetrace_logic().req_exp_start_signal.connect(
            self._mw.req_start_timetrace,
            Qt.QueuedConnection
        )

        # Show the main window and raise it above all others
        self._mw.previous_button.clicked.emit()
        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    @Slot(str)
    def change_current_file_labels(self, filepath: str) -> None:

        head, filename = os.path.split(filepath)
        self._mw.cps_plot.setTitle(filename, **{'size': '7pt'})
        self._mw.filename_label.setText(filename)

    @Slot(str, int)
    def update_statusbar(self, message: str, timeout: int = 5000) -> None:
        self._mw.statusbar.showMessage(message)

    @Slot()
    def export_plot(self):
        
        fig = plot.timetrace_plot(
            x_data=self._timetrace_logic().data.time_array,
            counts=self._timetrace_logic().data.counts
        )
        fig.show()

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
