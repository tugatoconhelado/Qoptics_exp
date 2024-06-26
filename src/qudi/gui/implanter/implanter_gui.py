# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.implanter.implanter_mainwindow import ImplanterMainWindow
from qudi.logic import filemanager
import functools


class ImplanterGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _pump_logic = Connector(name='pump_logic', interface='PumpLogic')


    def on_activate(self) -> None:
        self._mw = ImplanterMainWindow()
        self._mw.turn_on_button.clicked.connect(
            self._pump_logic().start_pump,
            Qt.QueuedConnection
        )
        self._mw.connect_button.clicked.connect(
            self._pump_logic().connect_pump,
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