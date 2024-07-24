# -*- coding: utf-8 -*-

import os
from PySide2.QtCore import Slot, Signal, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.odmr.odmr_mainwindow import ODMRMainWindow, SignalGeneratorConnection
import functools


class ODMRGui(GuiBase):

    start_odmr_exp_signal = Signal(float, float, float, int)
    stop_experiment_signal = Signal()

    _odmr_logic = Connector(name='odmr_logic', interface='ODMRLogic')
    _signal_generator_hardware = Connector(name='SG384_hardware', interface='SG384Hardware')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self._mw = ODMRMainWindow()
        self.signal_generator_connection = SignalGeneratorConnection()

        # Connect GUI signals
        self._mw.connection_action.triggered.connect(
            self.signal_generator_connection.show,
            Qt.QueuedConnection
        )
        self._mw.start_button.clicked.connect(
            self.start_experiment,
            Qt.QueuedConnection
        )
        self._mw.stop_button.clicked.connect(
            self.stop_experiment,
            Qt.QueuedConnection
        )

        # Connect signals to logic
        # Signal generator connection
        self.signal_generator_connection.connect_signal.connect(
            self._signal_generator_hardware().open_device,
            Qt.QueuedConnection
        )
        self.signal_generator_connection.refresh_button.clicked.connect(
            self._signal_generator_hardware().get_all_instruments,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().devices_signal.connect(
            self.signal_generator_connection.update_device_list,
            Qt.QueuedConnection
        )

        # Signal generator control
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
                'deviation'
            ),
            Qt.QueuedConnection
        )       
        self._mw.mod_rate_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'modulation_rate'
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
                'modulation_function'
            ),
            Qt.QueuedConnection
        )
        self._mw.display_signal.connect(
            functools.partial(
                setattr,
                self._signal_generator_hardware(),
                'display'
            ),
            Qt.QueuedConnection
        )
        self._mw.outputs_enabled_signal.connect(
            self._signal_generator_hardware().set_outputs,
            Qt.QueuedConnection
        )

        # Signal generator response
        self._signal_generator_hardware().frequency_signal.connect(
            self._mw.freq_spinbox.setValue,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().deviation_signal.connect(
            self._mw.mod_span_spinbox.setValue,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().modulation_rate_signal.connect(
            self._mw.mod_rate_spinbox.setValue,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().phase_signal.connect(
            self._mw.phase_spinbox.setValue,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().amplitude_signal.connect(
            self._mw.ampl_spinbox.setValue,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().modulation_enable_signal.connect(
            self._mw.modulation_on_radiobutton.setChecked,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().modulation_type_signal.connect(
            self._mw.modulation_type_combobox.setCurrentIndex,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().modulation_function_signal.connect(
            self._mw.modulation_function_combobox.setCurrentIndex,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().display_signal.connect(
            self._mw.display_combobox.setCurrentIndex,
            Qt.QueuedConnection
        )
        self._signal_generator_hardware().outputs_enabled_signal.connect(
            self._mw.set_outputs,
            Qt.QueuedConnection
        )

        # File management
        self._mw.save_button.clicked.connect(
            self._odmr_logic().save_data,
            Qt.QueuedConnection
        )
        self._mw.save_action.triggered.connect(
            self._odmr_logic().save_data,
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            self._odmr_logic().load_data,
            Qt.QueuedConnection
        )
        self._mw.load_action.triggered.connect(
            self._odmr_logic().load_data,
            Qt.QueuedConnection
        )
        self._mw.save_as_action.triggered.connect(
            self._odmr_logic().save_data_as,
            Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            self._odmr_logic().load_previous_data,
            Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            self._odmr_logic().load_next_data,
            Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            self._odmr_logic().delete_file,
            Qt.QueuedConnection
        )

        # Experiment control
        self._odmr_logic().odmr_data_signal.connect(
            self._mw.update_odmr_plot,
            Qt.QueuedConnection
        )
        self.start_odmr_exp_signal.connect(
            self._odmr_logic().start_acquisition,
            Qt.QueuedConnection
        )
        self.stop_experiment_signal.connect(
            self._odmr_logic().stop_acquisition,
            Qt.QueuedConnection
        )
        
        self.show()

    def on_deactivate(self) -> None:
        self._mw.close()

    def start_experiment(self):

        frequency_center = float(self._mw.freq_spinbox.value())
        frequency_range = float(self._mw.mod_span_spinbox.value())
        power = float(self._mw.ampl_spinbox.value())
        number_points = int(self._mw.number_points_spinbox.value())

        self.start_odmr_exp_signal.emit(frequency_center, power, frequency_range, number_points)

    def stop_experiment(self):

        self.stop_experiment_signal.emit()


    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
