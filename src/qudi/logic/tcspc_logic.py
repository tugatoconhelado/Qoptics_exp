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
    #_template_hardware = Connector(name='template_hardware',
    #                               interface='TemplateInterface',
    #                               optional=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

    def on_activate(self) -> None:

        # Set up a Qt timer to send periodic signals according to _increment_interval
        self.__timer = QtCore.QTimer(parent=self)
        self.__timer.setInterval(1000 * 0.1)  # Interval in milliseconds
        self.__timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(self.send_data, QtCore.Qt.QueuedConnection)
        # Start timer
        self.__timer.start()

    def on_deactivate(self) -> None:
        # Stop timer and delete
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None

    def stop_measurement(self):
        self.__timer.stop()
        self.log.info('Measurement stopped')

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
        data = np.random.rand(1000)
        self.data = data
        self.sig_data.emit(data)
