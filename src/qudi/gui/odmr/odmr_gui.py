# -*- coding: utf-8 -*-

import os
from PySide2.QtCore import Slot, Signal, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.odmr.odmr_mainwindow import ODMRMainWindow
import functools


class ODMRGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    #_confocal_logic = Connector(name='confocal_logic', interface='ConfocalLogic')
    #_tracking_logic = Connector(name='tracking_logic', interface='TrackingLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self._mw = ODMRMainWindow()
        self.show()

    def on_deactivate(self) -> None:
        self._mw.close()

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()