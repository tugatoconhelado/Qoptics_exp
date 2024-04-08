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
import numpy as np
import bh_spc
from bh_spc import spcm
import time
import copy


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
    sig_data = Signal(np.ndarray)  # data signal

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization
        self.counter = 0

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
            status = self._tcspc_hardware().initialise_tcspc(simulation=True)
            self.log.info(f'Initialisation status: {status}')
            self._tcspc_hardware().clear_rates(0)
            self._tcspc_hardware().get_SPC_params_from_module(0)
            self.__rates_timer.start()

    def get_rates(self):

        rates = self._tcspc_hardware().read_rate_counter(0)
        rate_values = (
            rates.sync_rate,
            rates.cfd_rate,
            rates.tac_rate,
            rates.adc_rate
        )
        self.sig_rate_values.emit(rate_values)
        self.log.debug(f'Rates: {rate_values}')

    def start_fifo_measurement(self):

        self.log.info('Measurement started')

        self.time_bins = np.arange(4096)
        self.data = np.zeros(4096 - 1, dtype=np.uint32)
        #self.time_conversion = self._tcspc_hardware()._tcsps_params.tac_range / 4096

        #self.__timer.setInterval(1000 * self._tcspc_hardware()._tcspc_params.display_time)
        self._tcspc_hardware().init_fifo_measurement(0)
        self._tcspc_hardware().start_measurement(0)

        self.buf_size = 32768

        self.continue_acquisition = True
        self.counter = 0
        self.__timer.start()
           
    def stop_measurement(self):
        self.continue_acquisition = False
        self.__timer.stop()
        self.log.info('Stopping measurement')
        self._tcspc_hardware().stop_measurement(0)

    def pause_measurement(self):
        self.__timer.stop()
        self.log.info('Measurement paused')
        self._tcspc_hardware().pause_measurement(0)

    def restart_measurement(self):
        self.__timer.start()
        self.log.info('Measurement restarted')
        self._tcspc_hardware().restart_measurement(0)

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
                self._tcspc_hardware().set_SPC_param(key.upper(), value)
        self.get_parameters(params)

    @Slot(str, float or int or str or bool)
    def set_parameter(self, param: str, value):
        self.log.info(f'Setting parameter {param} to {value}')
        self._tcspc_hardware().set_SPC_param(param.upper(), value)
        value = self._tcspc_hardware().get_SPC_param(param.upper())
        self.sig_parameter.emit(param, value)

    @Slot(dict)
    def get_parameters(self, params: dict):

        self.log.info('Getting parameters from TCSPC module')
        for param in params.keys():
            params[param] = self._tcspc_hardware().get_SPC_param(param.upper())
            self.sig_parameter.emit(param, params[param])
        self.sig_parameters.emit(params)

    @Slot()
    def save_data(self):

        pass

    @Slot()
    def load_data(self):
        self.log.info('Data loaded')

    @Slot()
    def get_data(self):
            
            #with self._mutex:
            if self.continue_acquisition:

                status_code = self._tcspc_hardware().test_state(0)
                self.counter += 1
                
                data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                if len(data):
                    self.convert_data(data)
                print(f'Data length: {len(data)}')
                #if spcm.MeasurementState.STOPPED_ON_COLLECT_TIME in status_code:
                #    self.log.info('Collection time over')
                #    self.stop_measurement()
                #    with self._mutex:
                #        data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                #        if len(data):
                #            self.data.append(data)
                #        self.convert_data(self.data)

                if self.counter >= 6:
                    self.log.info(f'Counter equal {self.counter}')
                    self.stop_measurement()
                    print('Reading data')
                    with self._mutex:
                        data = self._tcspc_hardware().read_data_from_tcspc(0, self.buf_size)
                        if len(data):
                            self.convert_data(data)

    def convert_data(self, data):

        print('Converting data')
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
        self.data = self.data + histogram
        print(self.data)
        print(self.data.shape)
        self.sig_data.emit(copy.copy(self.data))