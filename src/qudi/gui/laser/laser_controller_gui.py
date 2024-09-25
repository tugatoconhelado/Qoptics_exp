# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.laser.laser_controler_mainwindow import LaserControllerMainWindow
from qudi.logic import filemanager
from qudi.logic import plot
import functools


class LaserControllerGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _laser_controller_logic = Connector(name='laser_controller_logic', interface='LaserControllerLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        # initialize the main window
        self._mw = LaserControllerMainWindow()

        # connect all GUI internal signals

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self._mw.laser_frequency_signal.connect(
            self._laser_controller_logic().set_frequency,
            QtCore.Qt.QueuedConnection
        )
        self._mw.laser_power_signal.connect(
            self._laser_controller_logic().set_power,
            QtCore.Qt.QueuedConnection
        )

        # Show the main window and raise it above all others

        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()


    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
