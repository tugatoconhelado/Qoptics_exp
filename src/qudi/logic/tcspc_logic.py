# -*- coding: utf-8 -*-

__all__ = ['TemplateLogic']

from PySide2 import QtCore
from datetime import datetime

from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
import numpy as np


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
    sig_data = QtCore.Signal(np.ndarray)  # data signal

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _tcspc_hardware = Connector(name='tcspc_hardware',
                                   interface='TCSPCHardware',
                                   optional=True)
    sig_parameters = QtCore.Signal(dict)
    sig_rate_values = QtCore.Signal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

    def on_activate(self) -> None:

        # Set up a Qt timer to send periodic signals according to _increment_interval
        self.__timer = QtCore.QTimer(parent=self)
        self.__timer.setInterval(1000 * 0.5)  # Interval in milliseconds
        self.__timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(self.send_data, QtCore.Qt.QueuedConnection)

        self.__rates_timer = QtCore.QTimer(parent=self)
        self.__rates_timer.setInterval(1000)  # Interval in milliseconds
        self.__rates_timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__rates_timer.timeout.connect(self.get_rates, QtCore.Qt.QueuedConnection)

        # Initialise hardware module
        self._tcspc_hardware().initialise_tcspc(mode=0)
        self._tcspc_hardware().clear_rates(0)

        self.__rates_timer.start()

    def on_deactivate(self) -> None:
        # Stop timer and delete
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None

        self.__rates_timer.stop()
        self.__rates_timer.timeout.disconnect()
        self.__rates_timer = None

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

    def start_measurement(self):

        self.log.info('Measurement started')

        print(f'Display time: {self._tcspc_hardware()._tcspc_params.display_time}')
        self.__timer.setInterval(1000 * self._tcspc_hardware()._tcspc_params.display_time)
        self._tcspc_hardware().configure_memory(0)
        self._tcspc_hardware().start_single_mode_measurement(0, 0)

        self.continue_acquisition = True
        self.__timer.start()
           
    def stop_measurement(self):
        self.continue_acquisition = False
        self.__timer.stop()
        self.log.info('Measurement stopped')
        self._tcspc_hardware().stop_measurement(0)

    def pause_measurement(self):
        self.__timer.stop()
        self.log.info('Measurement paused')
        self._tcspc_hardware().pause_measurement(0)

    def restart_measurement(self):
        self.__timer.start()
        self.log.info('Measurement restarted')
        self._tcspc_hardware().restart_measurement(0)

    @QtCore.Slot(dict)
    def set_parameters(self, params: dict):

        self.log.info(f'Setting parameters to {params}')
        for key, value in params.items():
            if key != 'mode':
                self._tcspc_hardware().set_SPC_params(key, value)
        self._tcspc_hardware().set_SPC_params_to_module(0)
        self.get_parameters(params)

    def get_parameters(self, params):

        self.log.info('Getting parameters')
        params = self._tcspc_hardware().get_SPC_params(params, 0)
        print(params)
        self.sig_parameters.emit(params)

    def save_data(self):

        # Instantiate text storage object and configure it
        data_storage = TextDataStorage(
            root_dir='C:\\EXP\\data\\TCSPC',
            comments='# ', 
            delimiter='\t',
            file_extension='.dat',
            column_formats=('.8f', '.15e'),
            include_global_metadata=True,
            image_format=ImageFormat.PNG
        )

        # Create example data
        x = np.linspace(0, 1, 1000)  # 1 sec time interval
        y = np.sin(2 * np.pi * 2 * x)  # 2 Hz sine wave
        data = np.asarray([x, y]).transpose()  # Format data into a single 2D array with x being the first 
                                            # column and y being the second column
                                            
        # Prepare a dict containing metadata to be saved in the file header
        metadata = {'sample_number': 42,
                    'batch'        : 'xyz-123'}

        # Create an explicit timestamp.
        timestamp = datetime.now()  # Usually you would use this
        print(timestamp)

        # Create a nametag to include in the file name (optional)
        nametag = 'LFT'

        # Create an iterable of data column header strings (optional)
        column_headers = ('time (ns)', 'Counts')

        # Create an arbitrary string of informal "lab notes" that is included in the file header
        notes = 'TCSPC lifetime measurement with BH SPC-130EM.'

        # Save data to file
        file_path, timestamp, (rows, columns) = data_storage.save_data(
            data, 
            timestamp=timestamp, 
            metadata=metadata, 
            notes=notes,
            nametag=nametag,
            column_headers=column_headers,
            column_dtypes=(float, float)
        )

        self.log.info('Saved TCSPC data to {}'.format(file_path))

    def load_data(self):
        self.log.info('Data loaded')

    def send_data(self):
        with self._mutex:
            if self.continue_acquisition:
                status_code = self._tcspc_hardware().test_state(0)

                if 'SPC_TIME_OVER' in status_code:
                    readed_data = self._tcspc_hardware().read_data_from_tcspc(0)
                    readed_data = np.array(readed_data)
                    status_code = self._tcspc_hardware().test_state(0)
                    self.data = readed_data
                    self.sig_data.emit(self.data)
                    self.stop_measurement()

                pause_status = self._tcspc_hardware().pause_measurement(0)
                status_code = self._tcspc_hardware().test_state(0)

                if pause_status > 0:
                    readed_data = self._tcspc_hardware().read_data_from_tcspc(0)
                    readed_data = np.array(readed_data)
                    self.data = readed_data
                    self.sig_data.emit(self.data)

                    self._tcspc_hardware().restart_measurement(0)