# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.pump.pump_mainwindow import PumpMainWindow
from qudi.logic import filemanager
import functools


class PumpGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _pump_logic = Connector(name='pump_logic', interface='PumpLogic')


    def on_activate(self) -> None:
        self._mw = PumpMainWindow()
        self._mw.turn_on_button.clicked.connect(
            self._pump_logic().start_pump,
            Qt.QueuedConnection
        )
        self._mw.conect_signal.connect(
            self._pump_logic().connect_pump,
            Qt.QueuedConnection
        )

        self._mw.refresh_button.clicked.connect(
            self._pump_logic().refresh_ports,
            Qt.QueuedConnection
        )

        self._mw.disconnect_button.clicked.connect(
            self._pump_logic().disconnect_pump,
            Qt.QueuedConnection
        )

        
        self._pump_logic().refresh_ports_signal.connect(
            self._mw.refresh_ports,
            Qt.QueuedConnection
        )

        self._pump_logic().unlock_connect_signal.connect(
            self._mw.unlock_connect,
            Qt.QueuedConnection
        )

        self._pump_logic().lock_connect_signal.connect(
            self._mw.lock_connect,
            Qt.QueuedConnection
        )

        self._pump_logic().lock_connect_signal.connect(
            self._mw.create_parameter_combo_box,
            Qt.QueuedConnection
        )
        

        self._mw.parameter_signal.connect(
            self._pump_logic().get_parameter,
            Qt.QueuedConnection
        )

        self._pump_logic().update_parameter_signal.connect(
            self._mw.update_parameter,
            Qt.QueuedConnection
        )

        self._mw.get_parameter_for_setter_signal.connect(
            self._pump_logic().get_parameter_for_setter,
            Qt.QueuedConnection
        )

        self._pump_logic().update_parameter_for_setter_signal.connect(
            self._mw.update_parameter_for_setter,
            Qt.QueuedConnection
        )

        self._mw.set_parameter_signal.connect(
            self._pump_logic(),
            Qt.QueuedConnection
        )

        self.show()


    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.turn_on_button.clicked.disconnect()
        self._mw.close()

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
    
