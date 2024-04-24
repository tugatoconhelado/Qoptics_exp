# -*- coding: utf-8 -*-

import os
from PySide2.QtCore import Slot, Signal, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.odmr.odmr_mainwindow import ODMRMainWindow
import functools


class ODMRGui(GuiBase):

    _odmr_logic = Connector(name='odmr_logic', interface='ODMRLogic')
    _signal_generator_hardware = Connector(name='SG384_hardware', interface='SG384Hardware')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self._mw = ODMRMainWindow()

        # Connect signals to logic

        self._mw.freq_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'frequency'
            ),
            Qt.QueuedConnection
        )
        self._mw.mod_span_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'sweep_deviation'
            ),
            Qt.QueuedConnection
        )       
        self._mw.mod_rate_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'modulation_sweep_rate'
            ),
            Qt.QueuedConnection
        )
        self._mw.phase_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'phase'
            ),
            Qt.QueuedConnection
        )
        self._mw.ampl_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'amplitude'
            ),
            Qt.QueuedConnection
        )
        self._mw.modulation_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'modulation_enable'
            ),
            Qt.QueuedConnection
        )
        self._mw.modulation_type_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'modulation_type'
            ),
            Qt.QueuedConnection
        )
        self._mw.modulation_function_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'sweep_modulation_function'
            ),
            Qt.QueuedConnection
        )





        self.show()

    def on_deactivate(self) -> None:
        self._mw.close()

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()