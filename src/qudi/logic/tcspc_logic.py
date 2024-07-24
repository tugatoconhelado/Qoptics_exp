# -*- coding: utf-8 -*-

__all__ = ['TemplateLogic']

from PySide2.QtCore import QTimer, Qt, Signal, Slot
from datetime import datetime

from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
import numpy as np
import bh_spc
from bh_spc import spcm
import time
import copy
import dataclasses
import os


@dataclasses.dataclass
class TCSPCParameterData:

    display_time = 0
    collect_time = 0

@dataclasses.dataclass
class TCSPCData:

    time_bins: np.ndarray = np.array([])
    histogram: np.ndarray = np.array([])
    parameters: TCSPCParameterData = TCSPCParameterData()


# qudi logic measurement modules must inherit qudi.core.module.LogicBase or other logic modules.
class TCSPCLogic(LogicBase):
    """ This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """

    # Declare signals to send events to other modules connecting to this module
    data_signal = Signal(np.ndarray, np.ndarray)  # data signal
    status_sig = Signal(spcm.MeasurementState)
    file_changed_signal = Signal(str)
    track_point_signal = Signal()
    progress_signal = Signal(int)

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _tcspc_hardware = Connector(name='tcspc_hardware',
                                   interface='TCSPCHardware',
                                   optional=True)
    sig_parameters = Signal(dict)
    sig_rate_values = Signal(tuple)
    sig_parameter = Signal(str, float or int or str or bool)
    measurement_finished_signal = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization
        self.counter = 0
        self.data = TCSPCData()
        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='lifetime',
            exp_str='LFT'
        )
        self.track_intensity = False
        self.measurement_paused = False
        self.skip_next_rate = False

    def on_activate(self) -> None:

        # Set up a Qt timer to send periodic signals according to _increment_interval
        self.__timer = QTimer(parent=self)
        self.__timer.setInterval(1000 / 2)  # Interval in milliseconds
        self.__timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(self.get_data, Qt.QueuedConnection)

        self.__rates_timer = QTimer(parent=self)
        self.__rates_timer.setInterval(1000)  # Interval in milliseconds
        self.__rates_timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__rates_timer.timeout.connect(self.get_rates, Qt.QueuedConnection)


    def on_deactivate(self) -> None:
        # Stop timer and delete
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None

        self.__rates_timer.stop()
        self.__rates_timer.timeout.disconnect()
        self.__rates_timer = None

    def init_spc(self):

        print('Initialising TCSPC hardware')
        with self._mutex:
            status = self._tcspc_hardware().initialise_tcspc(simulation=False)
            self.log.info(f'Initialisation status: {status}')
            self._tcspc_hardware().clear_rates(0)
            self._tcspc_hardware().get_SPC_params_from_module(0)
            self.__rates_timer.start()
            self.get_all_parameters()

    def start_track_intensity(self, intensity_percent, reference_intensity):

        self.reference_intensity = reference_intensity
        self.intensity_percent = 100 - intensity_percent
        self.track_intensity = True
        print(f'Starting intensity tracking with threshold {intensity_percent}% and reference intensity {reference_intensity}')
        self.skip_next_rate = True
        if self.measurement_paused:
            self.restart_measurement()
        if not self.__rates_timer.isActive():
            self.__rates_timer.start()

    def get_rates(self):

        with self._mutex:
            rates = self._tcspc_hardware().read_rate_counter(0)
            self.rate_values = (
                rates.sync_rate,
                rates.cfd_rate,
                rates.tac_rate,
                rates.adc_rate
            )
            self.sig_rate_values.emit(self.rate_values)
            self.log.debug(f'Rates: {self.rate_values}')
            if self.skip_next_rate:
                self.skip_next_rate = False
                return
            if self.track_intensity:
                print(self.rate_values[1], self.reference_intensity * self.intensity_percent / 100)
                if self.rate_values[1] < self.reference_intensity * self.intensity_percent / 100:
                    self.log.info('Intensity dropped below threshold')
                    if self.continue_acquisition:
                        self.log.info('Pausing measurement')
                        self.pause_measurement()
                        self.track_intensity = False
                        self.track_point_signal.emit()

    def start_fifo_measurement(self):

        self.log.info('Measurement started')

        self.time_bins = np.arange(4096)
        self.data.histogram = np.zeros(4096 - 1, dtype=np.uint32)
        tac_range = self._tcspc_hardware().get_SPC_param('tac_range')
        tac_gain = self._tcspc_hardware().get_SPC_param('tac_gain')
        display_time = self._tcspc_hardware().get_SPC_param('display_time')
        collect_time = self._tcspc_hardware().get_SPC_param('collect_time')
        
        self.data.parameters.display_time = display_time
        self.data.parameters.collect_time = collect_time

        self.time_conversion = tac_range / (4096 * tac_gain)

        self.__timer.setInterval(1000 * display_time)
        self._tcspc_hardware().init_fifo_measurement(0)
        self._tcspc_hardware().start_measurement(0)

        self.buf_size = 32768

        self.progress = 0
        self.time_left = collect_time
        self.time_from_start = 0
        self.progress_signal.emit(self.progress)
        self.continue_acquisition = True
        self.measurement_paused = False
        self.counter = 0
        self.max_counter = int(collect_time / display_time)
        self.start_time = time.monotonic()
        self.__timer.start()
    
    @Slot()
    def track_interval_triggered(self):

        self.pause_measurement()
        self.track_point_signal.emit()

    @Slot()
    def stop_measurement(self):
        self.continue_acquisition = False
        self.track_intensity = False
        self.measurement_paused = False
        self.__timer.stop()
        self.log.info('Stopping measurement')
        self._tcspc_hardware().stop_measurement(0)

    @Slot()
    def pause_measurement(self):
        self.continue_acquisition = False
        self.measurement_paused = True
        self.__timer.stop()
        self.log.info('Measurement paused')
        self._tcspc_hardware().stop_measurement(0)

    @Slot()
    def restart_measurement(self):

        self.time_left = self._tcspc_hardware().get_SPC_param('collect_time') - self.elapsed_time
        self.time_from_start += self.elapsed_time
        self._tcspc_hardware().set_SPC_param('collect_time', self.time_left)
        setted_time_left = self._tcspc_hardware().get_SPC_param('collect_time')
        self._tcspc_hardware().start_measurement(0)
        self.start_time = time.monotonic()
        self.__timer.start()
        self.continue_acquisition = True
        self.measurement_paused = False
        self.log.info('Measurement restarted')
        
    @Slot(dict)
    def set_parameters(self, params: dict):
        """
        Set the parameters to the TCSPC module.

        Iterates over the `params` dictionary and sets the
        parameters individually to the TCSPC Hardware data
        structure. Then, it sets all the parameters to the
        TCSPC module. Finally, it gets the parameters 
        actually set from the TCSPC module.
        
        Args:
        params: dict
            The parameters to set
        """
        self.log.info(f'Setting parameters to {params}')
        for key, value in params.items():
            if key != 'mode':
                self.set_parameter(key.upper(), value)
        self.get_parameters(params)

    @Slot(str, int or float or str or bool)
    def set_parameter(self, param: str, value):
        self.log.info(f'Setting parameter {param} to {value}')
        self._tcspc_hardware().set_SPC_param(param.upper(), value)
        setted_value = self._tcspc_hardware().get_SPC_param(param.upper())
        self.sig_parameter.emit(param, setted_value)

    @Slot(dict)
    def get_parameters(self, params: dict):

        self.log.info('Getting parameters from TCSPC module')
        for param in params.keys():
            params[param] = self._tcspc_hardware().get_SPC_param(param.upper())
            self.sig_parameter.emit(param, params[param])
        self.sig_parameters.emit(params)

    def get_all_parameters(self):

        for param, val in self._tcspc_hardware().get_SPC_params_from_module(0).items():
            self.sig_parameter.emit(param, val)

    @Slot()
    def get_data(self):
            
            #with self._mutex:
            if self.continue_acquisition:

                status_code = self._tcspc_hardware().test_state(0)
                self.status_sig.emit(status_code)
                
                with self._mutex:
                    data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                    if len(data):
                        self.convert_data(data)
                
                if spcm.MeasurementState.STOPPED_ON_COLLECT_TIME in status_code:
                    self.log.info('Collection time over')
                    self.measurement_finished_signal.emit()
                    self.stop_measurement()
                    with self._mutex:
                        data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                        if len(data):
                            self.convert_data(data)

                #if self.counter >= 6:
                #    self.log.info(f'Counter equal {self.counter}')
                #    self.stop_measurement()
                #    with self._mutex:
                #        data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                #        if len(data):
                #            self.convert_data(data)
                
                self.elapsed_time = time.monotonic() - self.start_time
                self.progress = (self.elapsed_time + self.time_from_start)  / self.data.parameters.collect_time * 100
                print(f'Progress: {self.progress}')
                self.progress_signal.emit(min(self.progress, 100))


    def convert_data(self, data):

        records = np.array(data).view(np.uint32)
        photons = np.extract(np.bitwise_and(records, 0b1001 << 28) == 0, records)
        max_12bit = (1 << 12) - 1  # 4095
        microtimes = np.bitwise_and(np.right_shift(photons, 16), max_12bit)
        # Reverse the microtimes by subtracting from the max value, because the raw
        # microtime is measured from photon to SYNC, not SYNC to photon.
        microtimes = max_12bit - microtimes

        # Create the histogram
        histogram, bin_edges = np.histogram(microtimes, bins=self.time_bins)
        bin_edges = bin_edges[:-1]
        self.data.histogram = self.data.histogram + histogram

        time_bins = self.time_bins * self.time_conversion
        self.data.time_bins = time_bins[:-1]
        self.data_signal.emit(time_bins[:-1], copy.copy(self.data.histogram))

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
            self.data_signal.emit(self.data.time_bins, self.data.histogram)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.time_bins, self.data.histogram)
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
            self.data_signal.emit(self.data.time_bins, self.data.histogram)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')
