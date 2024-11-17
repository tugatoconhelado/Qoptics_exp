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


class LaserControllerLogic(LogicBase):
    """ This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """


    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _bh_laser_hardware = Connector(name='bh_laser_hardware', interface='BHLaserHardware')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization


    def on_activate(self) -> None:
        
        self._bh_laser_hardware().frequency = 0
        self._bh_laser_hardware().power = 1
        self._bh_laser_hardware().on_off_status = True

    def on_deactivate(self) -> None:
        # Stop timer and delete
        #self.__timer.stop()
        #self.__timer.timeout.disconnect()
        #self.__timer = None
        pass

    @Slot(float)
    def set_power(self, power: float) -> None:
        self._bh_laser_hardware().power = power

    @Slot(int)
    def set_frequency(self, frequency: int) -> None:
        self._bh_laser_hardware().frequency = frequency
