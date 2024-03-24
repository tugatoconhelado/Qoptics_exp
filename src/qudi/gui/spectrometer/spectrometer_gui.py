# -*- coding: utf-8 -*-

__all__ = ['SpectrometerGui']

import os
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QDialog, QWidget

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.spectrometer.spectrometer_mainwindow_gui import SpectrometerMainWindow
import functools


class SpectrometerGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    sigAddToCounter = Signal(int)  # add an integer value to the counter value
    _spectrometer_logic = Connector(name='spectrometer_logic', interface='SpectrometerLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        self.current_unit = 'wavelength'
        self.measurement_unit = 'nm'
        # initialize the main window
        self._mw = SpectrometerMainWindow()

        # connect all GUI internal signals
        self._mw.target_point_average.sigPositionChanged.connect(
            self.update_target_point_label,
            Qt.QueuedConnection
        )
        self._mw.target_point_current.sigPositionChanged.connect(
            self.update_target_point_label,
            Qt.QueuedConnection
        )
        self._mw.energy_radio_button.toggled.connect(self.request_unit_change)
        self._mw.wavelength_radio_button.toggled.connect(self.request_unit_change)
        self._mw.wavenumber_radio_button.toggled.connect(self.request_unit_change)

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        # Initialise spectrometer
        self._mw.initialise_button.clicked.connect(
            self._spectrometer_logic().initialise_spectrometer,
            Qt.QueuedConnection
        )

        # Connect experiment execution events (button press) to slots
        # True: single spectrum
        # False: read 'forever'
        self._mw.start_experiment_signal.connect(
            self._spectrometer_logic().start_acquisition,
            Qt.QueuedConnection
        )

        # Stop acquisition (different to close experiment)
        self._mw.stop_button.clicked.connect(
            self._spectrometer_logic().stop_acquisition,
            Qt.QueuedConnection
        )

        # Disable parameter editing when experiment is running
        self._spectrometer_logic().spectrometer_connection_status.connect(
            self._mw.update_status_gui,
            Qt.QueuedConnection
        )

        # Updates plot when spectrum is measured
        self._spectrometer_logic().spectrum_data_signal.connect(
            self._mw.update_spectrum_plot,
            Qt.QueuedConnection
        )
        self._spectrometer_logic().background_data_signal.connect(
            self._mw.update_background_spectrum,
            Qt.QueuedConnection
            )

        # Stores current averaged spectrum as background
        self._mw.store_background_button.clicked.connect(
            self._spectrometer_logic().set_background,
            Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            functools.partial(
                self._spectrometer_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_action.triggered.connect(
            functools.partial(
                self._spectrometer_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            functools.partial(
                self._spectrometer_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_action.triggered.connect(
            functools.partial(
                self._spectrometer_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.save_as_action.triggered.connect(
            functools.partial(
                self._spectrometer_logic().save_data_as
            ),
            Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            functools.partial(
                self._spectrometer_logic().load_data,
                -1
            ),
            Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            functools.partial(
                self._spectrometer_logic().load_data,
                1
            ),
            Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            functools.partial(
                self._spectrometer_logic().delete_file
            ),
            Qt.QueuedConnection
        )

        self._spectrometer_logic().file_changed_signal.connect(
            self.change_current_file_labels,
            Qt.QueuedConnection
        )
        self._spectrometer_logic().status_msg_signal.connect(
            self.update_statusbar,
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

    def show(self) -> None:
        """ Mandatory method to show the main window """
        self._mw.show()
        self._mw.raise_()

    def update_target_point_label(self):

        value = self._mw.target_point_current.value()
        value_str = f'{value:.2f} {self.measurement_unit}'
        self._mw.current_target_point_label.setText(
            f'Current spectrum indicator: {value_str}\n'
        )
        value = self._mw.target_point_average.value()
        value_str = f'{value:.2f} {self.measurement_unit}'
        self._mw.average_target_point_label.setText(
            f'Average spectrum indicator: {value_str}\n'
        )

    def request_unit_change(self):

        if self._mw.energy_radio_button.isChecked():
            unit = 'energy'
            unit_display = 'Energy (eV)'
            self.measurement_unit = 'eV'
        elif self._mw.wavenumber_radio_button.isChecked():
            unit = 'wavenumber'
            unit_display = 'Wavenumber (<math> cm<sup>-1</sup> </math>)'
            self.measurement_unit = 'cm^-1'
        elif self._mw.wavelength_radio_button.isChecked():
            unit = 'wavelength'
            unit_display = 'Wavelength (nm)'
            self.measurement_unit = 'nm'

        if unit != self.current_unit:
            self._spectrometer_logic().on_wavelength_unit_changed(
                unit, float(self._mw.laser_wavelength_spin_box.value())
            )
            self._mw.current_spectrum_plot.setLabel('bottom', unit_display)
            self._mw.average_spectrum_plot.setLabel('bottom', unit_display)
            self._mw.background_spectrum_plot.setLabel('bottom', unit_display)

            current_target_pos = self._mw.get_current_indicator_position_in_wavelength(self.current_unit)
            average_target_pos = self._mw.get_average_indicator_position_in_wavelength(self.current_unit)

            self._mw.move_current_target_point(
                self._spectrometer_logic().convert_units(
                    current_target_pos)
            )
            self._mw.move_average_target_point(
                self._spectrometer_logic().convert_units(
                    average_target_pos)
            )

            self.update_target_point_label()
            self.current_unit = unit

    @Slot(str)
    def change_current_file_labels(self, filepath: str) -> None:

        head, filename = os.path.split(filepath)
        self._mw.current_spectrum_plot.setTitle(filename, **{'size': '7pt'})
        self._mw.average_spectrum_plot.setTitle(filename, **{'size': '7pt'})
        self._mw.filename_label.setText(filename)
    

    @Slot(str, int)
    def update_statusbar(self, message: str, timeout: int = 5000) -> None:
        self._mw.statusbar.showMessage(message)