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



class IonGunLogic(LogicBase):
    refresh_ports_signal = Signal(list)
    unlock_connect_signal = Signal()
    lock_connect_signal = Signal()



    _ion_gun_hardware = Connector(name='ion_gun_hardware',
                                   interface='IonGunHardware'
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
    def connect_ion_gun(self, port_name: str):
        self._ion_gun_hardware().connect(device_id=1, port = self.dict_ports[port_name])
        if self._ion_gun_hardware().connected:
            self.lock_connect_signal.emit()

    @Slot()
    def disconnect_ion_gun(self):
        self._ion_gun_hardware().disconnect()
        if not self._ion_gun_hardware().connected:
            self.unlock_connect_signal.emit()
            

    @Slot()
    def refresh_ports(self):
        list_ports= self._ion_gun_hardware().devices
        self.dict_ports = {}
        for port in list_ports:
            port_name = port.split("::")[0]
            self.dict_ports[port_name] = port
        ports_names = list(self.dict_ports.keys())
        self.refresh_ports_signal.emit(ports_names)
        if not self._ion_gun_hardware().connected:
            self.unlock_connect_signal.emit()

    @Slot(str)
    def get_parameter(self, parameter_name: str):

        parameter_read = self._ion_gun_hardware().get_parameter(parameter_name)
        value = parameter_read['payload']
        data_type = self._ion_gun_hardware().commands[parameter_name]['data type']

        max_value = self._ion_gun_hardware().commands[parameter_name]['max']
        description = self._ion_gun_hardware().commands[parameter_name]['description']

        if value.isdigit():
            value = int(value)
            if data_type == 2:
                if max_value == 9999.99:
                    value = value/100

                elif max_value == 1:
                    value = value/100000
                elif max_value == 100:
                    value = value/100
            if data_type == 0:
                if value == 0:
                    value = "OFF"
                else:
                    value = "ON"
            if '(' in description:
                unit = description.split('(')[1].split(')')[0]
                value = str(value) + " " + unit

        
        value = str(value)

        self.update_parameter_signal.emit(value, description)
    
    @Slot(str)
    def get_parameter_for_setter(self, parameter_name: str):
        parameter_read = self._ion_gun_hardware().get_parameter(parameter_name)
        value = parameter_read['payload']
        data_type = self._ion_gun_hardware().commands[parameter_name]['data type']
        max_value = self._ion_gun_hardware().commands[parameter_name]['max']
        if value.isdigit():
            value = float(int(value))
            if data_type == 2:
                if max_value == 9999.99:
                    value = value/100
                elif max_value == 1:
                    value = value/100000
                elif max_value == 100:
                    value = value/100
        else:
            value = -1
        

        self.update_parameter_for_setter_signal.emit(value)
    
    @Slot(str, float)
    def set_parameter(self, parameter_name: str, value: float):
        data_type = self._ion_gun_hardware().commands[parameter_name]['data type']
        max_value = self._ion_gun_hardware().commands[parameter_name]['max']
        if data_type == 2:
            if max_value == 9999.99:
                value = value*100
            elif max_value == 1:
                value = value*100000
            elif max_value == 100:
                value = value*100
        value = int(value)
        response = self._ion_gun_hardware().set_parameter(parameter_name, value)
        value = response['payload']
        #Create a funtion for this part, is the same as get_parameter
        data_type = self._ion_gun_hardware().commands[parameter_name]['data type']
        max_value = self._ion_gun_hardware().commands[parameter_name]['max']
        if value.isdigit():
            value = float(int(value))
            if data_type == 2:
                if max_value == 9999.99:
                    value = value/100
                elif max_value == 1:
                    value = value/100000
                elif max_value == 100:
                    value = value/100
        self.update_parameter_for_setter_signal.emit(value)
        #self.get_parameter_for_setter(parameter_name)
        
        

        