# -*- coding: utf-8 -*-

__all__ = ['TimeTraceGui']

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.ion_gun.ion_gun_mainwindow import IonGunMainWindow
from qudi.logic import filemanager
import functools


class IonGunGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    _ion_gun_logic = Connector(name='ion_gun_logic', interface='IonGunLogic')


    def on_activate(self) -> None:
        self._mw = IonGunMainWindow()
        
        self._mw.conect_signal.connect(
            self._ion_gun_logic().connect_ion_gun,
            Qt.QueuedConnection
        )

        self._mw.refresh_button.clicked.connect(
            self._ion_gun_logic().refresh_ports,
            Qt.QueuedConnection
        )

        self._mw.disconnect_button.clicked.connect(
            self._ion_gun_logic().disconnect_ion_gun,
            Qt.QueuedConnection
        )

        self._mw.parameter_signal.connect(
            self._ion_gun_logic().get_parameter,
            Qt.QueuedConnection
        )
        
        self._mw.no_parameter_signal.connect(
            self._ion_gun_logic().set_no_parameter,
            Qt.QueuedConnection
        )

        self._ion_gun_logic().refresh_ports_signal.connect(
            self._mw.refresh_ports,
            Qt.QueuedConnection
        )

        self._ion_gun_logic().unlock_connect_signal.connect(
            self._mw.unlock_connect,
            Qt.QueuedConnection
        )

        self._ion_gun_logic().lock_connect_signal.connect(
            self._mw.lock_connect,
            Qt.QueuedConnection
        )

        self._ion_gun_logic().lock_connect_signal.connect(
            self._mw.create_parameter_combo_box,
            Qt.QueuedConnection
        )
        
        self._ion_gun_logic().update_parameter_signal.connect(
            self._mw.update_parameter,
            Qt.QueuedConnection
        )

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
    
