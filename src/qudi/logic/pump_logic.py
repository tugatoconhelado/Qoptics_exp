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



class PumpLogic(LogicBase):
    _pump_hardware = Connector(name='pump_hardware',
                                   interface='PumpHardware'
                                   )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        # Stop timer and delete
        #self.__timer.stop()
        #self.__timer.timeout.disconnect()
        #self.__timer = None
        pass

    @Slot()
    def hello_world(self):
        print("Hello World")

    @Slot()
    def start_pump(self):
        self._pump_hardware().send_message(self._pump_hardware().commands['PumpgStatn'],True)

    @Slot()
    def stop_pump(self):
        self._pump_hardware().send_message(self._pump_hardware().commands['PumpgStatn'],False)

    @Slot()
    def connect_pump(self):
        self._pump_hardware().connect()