import numpy as np
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QApplication
import os
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
import datetime

import dataclasses

@dataclasses.dataclass
class TimeTraceParameterData:
    """
    Contains the parameters of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    sampling_frequency : int
    refresh_time : float
    window_time : float
    """
    sampling_frequency: int = 1000
    refresh_time: float = 0.1
    window_time: float = 10.0


@dataclasses.dataclass
class TimeTraceData:
    """
    Contains the data of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    parameters : TimeTraceParameterData
    counts : numpy.ndarray
    time_array : numpy.ndarray
    """
    parameters: TimeTraceParameterData = None
    counts: np.ndarray = np.ones(1000)
    time_array: np.ndarray = np.arange(1000)

class TimeTraceLogic(LogicBase):
    """ This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """
    status_msg_signal = Signal(str)
    data_signal = Signal(np.ndarray, np.ndarray)
    experiment_status_signal = Signal(bool)
    file_changed_signal = Signal(str)
    track_point_signal = Signal()
    req_exp_start_signal = Signal()

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _apd_hardware = Connector(name='apd_hardware',
                                   interface='APDHardware',
                                   optional=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        parameters = TimeTraceParameterData()
        self.data = TimeTraceData(parameters=parameters)
        self.measure = False
        self.track_intensity = False

        self.time_counter = 0
        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='timetrace',
            exp_str='TMT'
        )

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        # Stop timer and delete
        #self.__timer.stop()
        #self.__timer.timeout.disconnect()
        #self.__timer = None
        pass

    @Slot(int, float)
    def on_start_track_intensity(self, intensity_percent, reference_intensity):

        self._timetrace_logic().start_track_intensity(intensity_percent, reference_intensity)
        self._mw.req_start_timetrace()

    @Slot(int, float)
    def start_track_intensity(self, intensity_percent, reference_intensity) -> None:
        self.track_intensity = True
        self.intensity_threshold = 100 - intensity_percent
        self.reference_intensity = reference_intensity
        self.log.info(f'Starting intensity tracking with threshold {intensity_percent}% and reference intensity {reference_intensity}')

    @Slot(int, float, float)
    def start_acquisition(self, samp_freq: int, refresh_time : float, window_time: float) -> None:
        """
        Starts the acquisition.

        Calls the `start_apd` method of `APD` with the currently registered
        paramaters.
        Creates the containers in the `data` attribute and emits the
        `experiment_status_signal` signal with True to norigy that the experiment
         is running.
        """
        self.data.parameters.sampling_frequency = samp_freq
        self.data.parameters.refresh_time = refresh_time
        self.data.parameters.window_time = window_time
        self.status_msg_signal.emit(f'TimeTrace: Starting Acquisition with parameters: {self.data.parameters}')
        self.measure = True

        # Array to store the time
        self.data.time_array = np.zeros(
            int(self.data.parameters.window_time / self.data.parameters.refresh_time)
        )

        # Array to store the data
        self.data.counts = np.zeros(
            int(self.data.parameters.window_time / self.data.parameters.refresh_time)
        )

        self.log.info(f'Starting Acquisition')
        self.log.info(f'Setting Parameters')
        self.log.info(f'------------------')
        self.log.info(f'Sampling Frequency: {self.data.parameters.sampling_frequency}')
        self.log.info(f'Refresh Time: {self.data.parameters.refresh_time}')
        self.log.info(f'Window Time: {self.data.parameters.window_time}')
        
        self.experiment_status_signal.emit(True)

        frequency = self.data.parameters.sampling_frequency
        samples = int(
            self.data.parameters.sampling_frequency
            * self.data.parameters.refresh_time
        )
        duty_cycle = 0.5

        clock, counter = self._apd_hardware().set_apd(
            frequency=frequency,
            samples=samples,
            continuous=True
        )

        clock.start()
        counter.start()

        self.time_counter = 0
        samples = (
            self.data.parameters.refresh_time
            * self.data.parameters.sampling_frequency
        )
        while self.measure:
            
            read_data = self.get_fluorescence(
                    samples = samples,
                    frequency = self.data.parameters.sampling_frequency,
                    time_out = self.data.parameters.refresh_time * 1.2
            )

            self.time_counter += 1

            if self.track_intensity:
                self.log.debug(f'Intensity: {np.average(read_data)}' +
                    f' Reference: {self.reference_intensity * self.intensity_threshold / 100}')
                if np.average(read_data) < self.reference_intensity * self.intensity_threshold / 100:
                    self.log.info(f'Intensity {np.average(read_data)} below threshold {self.reference_intensity * self.intensity_threshold / 100}')
                    self.stop_acquisition()
                    self.track_point_signal.emit()

            QApplication.processEvents()

    def get_fluorescence(self, samples: int, frequency: int, time_out: float) -> float:
        """
        It acquires the last `acquisition_time` data

        In order to do so it computes the number of samples to be read from
        the NI card as `acquisition_time` times `frequency`

        Parameters
        ----------
        acquisition_time : float
            Exposure time of the data to be acquired
        frequency : int
            Sampling frequency to make the acquisition. Must be the same used
            in the `start_apd()` method
        time_out : float
            Time that NI card wil wait to read data before raising and error

        Returns
        -------
        mean_counts : float
            The mean of the measured counts for the given acquisition_time
        """
        counts = self._apd_hardware().get_fluorescence(
            samples=samples,
            frequency=frequency,
            time_out=time_out,
        )        
        counts = np.diff(counts)
        counts = counts #/ 1000
        # Each datum in the array corresponds to
        # refresh_time / (frequency * refresh_time) seconds so we must multiply
        # by frequency to have each datum correspond to 1 second (counts per s)
        mean_counts = np.mean(counts)

        self.log.debug(f'Returning {mean_counts}')

        self.data.counts[0] = mean_counts
        self.data.counts = np.roll(self.data.counts, -1)

        # So that the graph does not have a (0,0) start
        if self.time_counter == 0:
            self.data.counts[0:-1] += self.data.counts[-1]

        self.data.time_array[0] = self.time_counter * self.data.parameters.refresh_time
        self.data.time_array = np.roll(self.data.time_array, -1)

        self.data_signal.emit(self.data.time_array, self.data.counts)

        return self.data.counts

    def stop_acquisition(self, *args):
        """
        Stops the measurement.

        Sets `self.measure` to `False`, emits the signal with the status of the
        experiment (False). Calls the `close_apd` method of `APD`.
        """
        self.status_msg_signal.emit('TimeTrace: Stopping Acquisition')
        self.measure = False
        self.experiment_status_signal.emit(False)
        self.track_intensity = False

        self._apd_hardware().stop()

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

    def load_data(self):

        data, metadata, general, filepath = self.filemanager.load()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.time_array, self.data.counts)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.time_array, self.data.counts)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath

    def load_next_data(self):

        data, metadata, general, filepath = self.filemanager.load_next()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.time_array, self.data.counts)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')