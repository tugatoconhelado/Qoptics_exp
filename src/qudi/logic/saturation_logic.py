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
class SaturationParameterData:
    """
    Contains the parameters of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    sampling_frequency : int
    refresh_time : float
    window_time : float
    """
    points: int = 1000
    laser: str = ''


@dataclasses.dataclass
class SaturationData:
    """
    Contains the data of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    parameters : TimeTraceParameterData
    counts : numpy.ndarray
    time_array : numpy.ndarray
    """
    parameters: SaturationParameterData = None
    power: np.ndarray = np.ones(1000)
    counts: np.ndarray = np.arange(1000)

class SaturationLogic(LogicBase):
    """ Logic module for the measurement of Saturation.

    This module is responsible for the acquisition of the data and the
    communication with the hardware module. It also handles the saving and
    loading of the data.

    The logic module is connected to the GUI module through the signals and
    slots mechanism. The GUI module sends signals to the logic module to start
    and stop the acquisition and the logic module sends signals to the GUI module
    to update the plot and the status message.

    The logic module is connected to the hardware module through the `APDHardware`
    connector. The `APDHardware` module is responsible for the communication with
    the NI card.

    Attributes
    ----------
    _apd_hardware : Connector
        Connector to the `APDHardware` module
    _mutex : Mutex
        Mutex for access serialization
    data : SaturationData
        Data container for the measurement
    measure : bool
        Flag to indicate if the measurement is running

    Methods
    -------
    on_activate()
        Method called when the module is activated
    on_deactivate()
        Method called when the module is deactivated
        
    """
    status_msg_signal = Signal(str)
    data_signal = Signal(np.ndarray, np.ndarray)
    experiment_status_signal = Signal(bool)
    file_changed_signal = Signal(str)
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
    _bh_laser_hardware = Connector(name='bh_laser_hardware', interface='BHLaserHardware')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        parameters = SaturationParameterData()
        self.data = SaturationData(parameters=parameters)
        self.measure = False

        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='timetrace',
            exp_str='TMT'
        )

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def set_parameters(self, points: int, laser: str):
        """
        Sets the parameters of the experiment.

        Parameters
        ----------
        points : int
            Number of points to be acquired
        laser : str
            Name of the laser to be used
        """
        self.data.parameters.points = points
        self.data.parameters.laser = laser

    @Slot(int, float, float)
    def start_acquisition(self) -> None:
        """
        Starts the acquisition.

        Calls the `start_apd` method of `APD` with the currently registered
        paramaters.
        Creates the containers in the `data` attribute and emits the
        `experiment_status_signal` signal with True to norigy that the experiment
         is running.
        """
        self.status_msg_signal.emit(f'TimeTrace: Starting Acquisition with parameters: {self.data.parameters}')
        self.measure = True

        if self.data.parameters.laser == 'BH Laser':
            self._bh_laser_hardware().frequency = 0
        else:
            self.log.error('Laser not recognized')
            return

        # Array to store the data
        self.data.counts = np.zeros(self.data.parameters.points)
        power_step = 10 / self.data.parameters.points
        self.data.power = np.zeros(self.data.parameters.points)

        for i in range(int(self.data.parameters.points)):
            if not self.measure:
                break
            if self.data.parameters.laser == 'BH Laser':
                self._bh_laser_hardware().power = i * power_step
                self.data.power[i] = self._apd_hardware().power

            counts = self._apd_hardware().get_current_counts()
            self.data.counts[i] = counts
            self.data_signal.emit(self.data.power, self.data.counts)
            QApplication.processEvents()

    def stop_acquisition(self, *args):
        """
        Stops the measurement.

        Sets `self.measure` to `False`, emits the signal with the status of the
        experiment (False). Calls the `close_apd` method of `APD`.
        """
        self.status_msg_signal.emit('Stopping Acquisition')
        self.measure = False
        self.experiment_status_signal.emit(False)

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
            self.data_signal.emit(self.data.power, self.data.counts)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.power, self.data.counts)
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
            self.data_signal.emit(self.data.power, self.data.counts)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')