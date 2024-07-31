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
    update_parameter_signal = Signal(str,str)



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

        self._ion_gun_hardware().connect(port = self.dict_ports[port_name])
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

        value = self._ion_gun_hardware().get_parameter(parameter_name)
        if value != None:
            if parameter_name == 'Error status':
                value = self.process_error_status(value)
            description = self._ion_gun_hardware().commands[parameter_name]['description']



            self.update_parameter_signal.emit(value, description)
    
    @Slot(str)
    def get_parameter_for_setter(self, parameter_name: str):
        pass
    
    @Slot(str, float)
    def set_parameter(self, parameter_name: str, value: float):
       
        
        response = self._ion_gun_hardware().set_parameter(parameter_name, value)
        
        #self.get_parameter_for_setter(parameter_name)

    @Slot(str)
    def process_error_status(self, error_status: str):
        error_list = error_status.split(';')
        value = ''
        for error in self._ion_gun_hardware().error_comands.keys():
            error_code = self._ion_gun_hardware().error_comands[error]['ASCII string']
            error_code += 'T'
            if error_code in error_list:
                value += error + ';'
        if value == '':
            value = 'No errors'
        return value
    
    @Slot(str)
    def set_no_parameter(self, parameter_name: str):
        responce = self._ion_gun_hardware().set_parameter(parameter_name, '')
        
        
        

        