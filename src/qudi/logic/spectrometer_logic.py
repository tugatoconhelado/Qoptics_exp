# -*- coding: utf-8 -*-

__all__ = ['TemplateLogic']

from PySide2.QtCore import Slot, Signal, QTimer

from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
import numpy as np
import copy
import seabreeze.spectrometers as sbSpectrometer
import dataclasses
import os
from qudi.logic.filemanager import FileManager

@dataclasses.dataclass
class SpectrumParameterData:
    """
    Contains the parameters related to the acquisition of an spectrum experiment
    
    Attributes
    ----------
    wrapper : SignalWrapper
        Contains a signal that indicates when a parameter is changed.
    integration_time : int
        Integration time in ms for the measurement.
    scans_average : int
        Number of scans to average.
    electrical_darl : bool
        Indicates if measurements are acquires with electrical dark correction.
    substract_background : bool
        Indicates if the background is substracted from the results.
    """

    integration_time: int = 100
    scans_average: int = 10
    electrical_dark: bool = True
    substract_background: bool = False
    laser_wavelength: float = 532.0

@dataclasses.dataclass
class SpectrumData:
    """
    Contains the data of the Spectrum Experiment
    
    Attributes
    ----------
    parameters : SpectrumParameterData
    wavelength : np.ndarray
    counts_time : np.ndarray
    background : np.ndarray
    spectrum : np.ndarray
    average : np.ndarray
    counts : np.ndarray
    """
    parameters: SpectrumParameterData = None
    wavelength: np.ndarray = None
    counts_time: np.ndarray = None
    background: np.ndarray = None
    spectrum: np.ndarray = None
    average: np.ndarray = None
    counts: np.ndarray = None


class SpectrometerLogic(LogicBase):
    """ This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """
    spectrum_data_signal = Signal(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    background_data_signal = Signal(np.ndarray, np.ndarray)
    spectrometer_connection_status = Signal(bool)
    status_msg_signal = Signal(str)
    file_changed_signal = Signal(str)
    change_unit_signal = Signal(str)
    # Declare signals to send events to other modules connecting to this module
    #sigCounterUpdated = QtCore.Signal(int)  # update signal for the current integer counter value

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    #_template_hardware = Connector(name='template_hardware',
    #                               interface='TemplateInterface',
    #                               optional=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        self.__length = 1000
        self.index = 0 # current index
        self.time_sum = 0 # current time
        parameters = SpectrumParameterData()
        self.data = SpectrumData(parameters=parameters)
        self.spectra = np.zeros((10, 10))
        self.single_measurement = False
        self.spectrometer = None
        self.measure = True
        self.unit = 'wavelength'

        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='spectra',
            exp_str='SPR'
        )
    def on_activate(self) -> None:

        # Set up a Qt timer to send periodic signals according to integration_time
        self.__timer = QTimer(parent=self)
        self.__timer.setInterval(self.data.parameters.integration_time * 1000)
        self.__timer.setSingleShot(False)

        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(self.get_spectrum)

        # Start timer
        #self.__timer.start()
        pass

    def on_deactivate(self) -> None:
        # Stop timer and delete
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None
        pass

    @Slot()
    def start_acquisition(self, integration_time : int, scans_average : int,
        electrical_dark : bool, substract_background : bool,
        laser_wavelength : float, single_measurement : bool = False
    ) -> None:
        """
        Starts the spectrum acquisition.

        For this, it sets the timer interval to the integration time,
        then creates the arrays that will contain the counts, the
        count_time and the spectra to average. Finally, it starts the
        experiment, contained in get_spectrum, which performs the acquisition.

        Parameters
        ----------
        single_measurement: bool
            Indicates wether to calculate a single measurement until the
            number of averaged spectra is equal to the number of scans to
            average, or read until the user stops the experiment.

        Returns
        -------
        None

        """
        # Sets wether to measure only requested number of averages or measure continuously
        self.single_measurement = single_measurement
        # Set the parameters in the data container
        self.data.parameters.integration_time = integration_time
        self.data.parameters.scans_average = scans_average
        self.data.parameters.electrical_dark = electrical_dark
        self.data.parameters.substract_background = substract_background
        self.data.parameters.laser_wavelength = laser_wavelength

        # Sets the parameters in the spectrometer
        self.spectrometer.integration_time_micros(integration_time * 1000)

        # Creates structure to store data
        self.spectra = np.zeros((self.data.parameters.scans_average, self.__length))
        self.data.average = np.zeros(self.__length)
        self.data.counts_time = np.array([])
        self.data.counts = np.array([])
        self.measure = True

        self.log.info(f'Starting Acquisition')
        self.log.info(f'Current Parameters')
        self.log.info(f'------------------')
        self.log.info(f'Integration time: {self.data.parameters.integration_time}')
        self.log.info(f'Scans to average: {self.data.parameters.scans_average}')
        self.log.info(f'Electrical dark: {self.data.parameters.electrical_dark}')
        self.log.info(f'Substract Background: {self.data.parameters.substract_background}')

        self.stop_acquisition()
        self.status_msg_signal.emit(f'Spectrometer: Starting Acquisition with parameters {self.data.parameters}')
        self.changed_integration_time = True
        self.__timer.setInterval(self.data.parameters.integration_time)
        self.__timer.start()

    def get_spectrum(self) -> None:
        """
        Handles the data acquiring. It esentially performs the experiment

        Records the spectrum and wavelengths from the spectrometer object.
        Each measured spectrum is averaged and the counts are computed as
        the sum of all the intensities recorded. Finally, it emits a
        spectrum_data_signal containing all the info stracted:
        """
        with self._mutex:
            if self.changed_integration_time is True:
                self.changed_integration_time = False
                return
            self.data.spectrum = self.spectrometer.intensities(
                    self.data.parameters.electrical_dark
                    )
            if self.data.parameters.substract_background:
                self.data.spectrum -= self.data.background
            self.data.wavelength = self.spectrometer.wavelengths()

            # Add to current average
            self.spectra = np.roll(self.spectra, 1, axis=0)
            self.spectra[-1, :] = self.data.spectrum
            if self.index == 0:
                self.spectra[:, :] = self.data.spectrum
            self.data.average = np.sum(self.spectra, axis=0) / (self.data.parameters.scans_average)

            # Now compute the counts
            self.time_sum += self.data.parameters.integration_time / 1000 # In seconds
            self.data.counts_time = np.append(
                    self.data.counts_time, self.time_sum
                    )
            counts = np.sum(self.data.spectrum * 1000 / self.data.parameters.integration_time)
            self.data.counts = np.append(self.data.counts, counts)

            self.send_measured_data(
                self.data.wavelength, self.data.spectrum, self.data.average,
                self.data.counts_time, self.data.counts
            )

            self.index += 1
            if self.single_measurement and (self.index == self.data.parameters.scans_average):
                self.stop_acquisition()

    def convert_units(self, wavelength: np.ndarray):
        """
        Converts between the diferent types of units for the x axis
        wavelength: as delivered by spectrometer
        energy: simple calculation with E = hc / lambda
        wavenumber: for raman spectroscopy with input laser wavelength
        computation is done as """

        wavelength = np.array(wavelength)
        if self.unit == 'energy':
            # Compute in energy
            hc = 1_239.8419 # in eV * nm
            energy = hc / wavelength # to eV
            x_data = energy

        elif self.unit == 'wavenumber':
            # Compute in wavenumber
            laser_wavelength = self.data.parameters.laser_wavelength
            laser_wavenumber = 10_000_000 / laser_wavelength
            wavenumber = 10_000_000 / wavelength
            raman_shift = laser_wavenumber - wavenumber
            x_data = raman_shift
        
        else:
            x_data = wavelength

        return x_data
    
    @Slot(str, float)
    def on_wavelength_unit_changed(self, unit: str = 'wavelength',
        laser_wavelength: float = 532.0) -> None:

        self.unit = unit
        self.data.parameters.laser_wavelength = laser_wavelength
        with self._mutex:
            self.send_measured_data(
                self.data.wavelength,
                self.data.spectrum,
                self.data.average,
                self.data.counts_time,
                self.data.counts
            )
            self.background_data_signal.emit(
                self.convert_units(wavelength=copy.copy(self.data.wavelength)),
                self.data.background
            )
            self.change_unit_signal.emit(unit)

    def send_measured_data(self, wavelength, spectrum, average, counts_time, counts):

        self.spectrum_data_signal.emit(
            self.convert_units(wavelength=wavelength),
            np.array(spectrum),
            np.array(average),
            np.array(counts_time),
            np.array(counts)
        )

    @Slot()
    def stop_acquisition(self) -> None:
        """
        Stops the timer if it is still running.

        Resets all the index counters and partial sums
        Emits a signal with the status of the experiment.
        True for experiment done and False for experiment running
        """
        self.status_msg_signal.emit(f'Spectrometer: Stopping Acquisition')
        if self.__timer.isActive():
            self.__timer.stop()
        self.measure = False
        self.index = 0
        self.time_sum = 0

    @Slot()
    def set_background(self):
        """
        Stores the current spectrum as the background
        """
        self.data.background = copy.copy(self.data.average)
        self.background_data_signal.emit(
            self.convert_units(wavelength=copy.copy(self.data.wavelength)),
            self.data.background
        )

    @Slot()
    def initialise_spectrometer(self) -> None:
        """
        Creates an instance of the spectrometer object.
        Stores the length of the data recorded. To do this, it stracts the
        wavelengths from the spectrometer, and calculates its length.
        Emits a signal to enable gui
        """

        self.log.info('Loading Spectrometer')
        if self.spectrometer is not None:
            self.spectrometer.close()
        try:
            spectrometers = sbSpectrometer.list_devices()
            if len(spectrometers) == 0:
                self.log.info('No spectrometer found')
                self.spectrometer_connection_status.emit(False)
                return
            else:
                self.spectrometer = sbSpectrometer.Spectrometer(spectrometers[0])
                limits = self.spectrometer.integration_time_micros_limits
                self.log.info(f'Loading Spectrometer {self.spectrometer}')
                self.__length = len(self.spectrometer.wavelengths())
                self.data.background = np.zeros(self.__length)
                self.spectrometer_connection_status.emit(True)
        except:
            self.log.info('Loading Spectrometer failed')
            self.spectrometer_connection_status.emit(False)

    def save_data(self, filepath: str = '') -> None:
        """
        Saves the data to a file.

        Parameters
        ----------
        filepath : str
            Path to the file where the data will be saved
        """
        data_dict = dataclasses.asdict(self.data)
        data_dict.pop('parameters')
        filepath = self.filemanager.save(
            data=data_dict,
            metadata=dataclasses.asdict(self.data.parameters)
        )
        self.log.info(f'Saved data to {filepath}')
        self.file_changed_signal.emit(filepath)
        return filepath

    def save_data_as(self):
        """
        Opens a file dialog to save the data to a file.
        """
        data_dict = dataclasses.asdict(self.data)
        data_dict.pop('parameters')
        filepath = self.filemanager.save_as(
            data=data_dict,
            metadata=dataclasses.asdict(self.data.parameters)
        )
        self.log.info(f'Saved data to {filepath}')
        self.file_changed_signal.emit(filepath)
        return filepath

    def load_data(self, move: int = 0):
        """
        Loads the data from a file.

        Parameters
        ----------
        move : int
            Indicates if the next or previous file will be loaded.
            If move is 0, a dialog will be loaded.
            If move is 1, the next file will be loaded.
            If move is -1, the previous file will be loaded.
        """
        if move == 0:
            data, metadata, general, filepath = self.filemanager.load()
        elif move == 1:
            data, metadata, general, filepath = self.filemanager.load_next()
        elif move == -1:
            data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.send_measured_data(
                self.convert_units(wavelength=copy.copy(self.data.wavelength)),
                self.data.spectrum,
                self.data.average,
                self.data.counts_time,
                self.data.counts
            )
            self.background_data_signal.emit(
                self.convert_units(wavelength=copy.copy(self.data.wavelength)),
                self.data.background
            )
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')