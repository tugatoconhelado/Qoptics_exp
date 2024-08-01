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
from time import sleep

import dataclasses

@dataclasses.dataclass
class ImplantationSpot:
    implantation_time: float = 0
    position_x: float = 0
    position_y: float = 0
    extra_parameter: dict  = {}

class ImplantationMatrix:
    def __init__(self):
        self.implantation_matrix = []
        self.sacrifice_point = (0,0)
        self.current_implantation_spot = ImplantationSpot()
    
    def add_implantation_spot(self,pos_x: float, pos_y: float, implantation_time: float):
        self.current_implantation_spot.position_x = pos_x
        self.current_implantation_spot.position_y = pos_y
        self.current_implantation_spot.implantation_time = implantation_time
        self.implantation_matrix.append(self.current_implantation_spot)
        self.current_implantation_spot = ImplantationSpot()

    def remove_implantation_spot(self):
        self.implantation_matrix.pop()
    

    def add_implantation_spot_parameter(self, parameter_name: str, value: float):
        self.current_implantation_spot.extra_parameter[parameter_name] = value
    
    def remove_implantation_spot_parameter(self, parameter_name: str):
        self.current_implantation_spot.extra_parameter.pop(parameter_name)
    
    def set_sacrifice_point(self, pos_x: float, pos_y: float):
        self.sacrifice_point = (pos_x, pos_y)

    
        


class IonGunLogic(LogicBase):
    refresh_ports_signal = Signal(list)
    unlock_connect_signal = Signal()
    lock_connect_signal = Signal()
    update_parameter_signal = Signal(str,str)
    update_parameter_for_setter_signal = Signal(float)



    _ion_gun_hardware = Connector(name='ion_gun_hardware',
                                   interface='IonGunHardware'
                                   )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.implantation_matrix = ImplantationMatrix()

        self.current_values = {'Emision current':10000,
                'Energy':5000,
                'Extractor voltage':90.01,
                'Focus 1 voltage':75.00,
                'Focus 2 voltage':0.00,
                'Position X':0,
                'Position Y':0,
                'Width X':0,
                'Width Y':0,
                'Blanking X':1,
                'Blanking Y':1,
                'Blanking level':0,
                'Time per dot':50,
                'Angle phi':0,
                'Angle theta':0,
                'L': 33000,
                'M': 11500,
                'Deflection X':48,
                'Deflection Y':67

        }


        

        
       
                
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
            unit = self._ion_gun_hardware().commands[parameter_name]['unit R']
            value = str(value) + ' ' + unit


            self.update_parameter_signal.emit(value, description)
    
    @Slot(str)
    def get_parameter_for_setter(self, parameter_name: str):
        value = self.current_values[parameter_name]
        self.update_parameter_for_setter_signal.emit(value)
    
    @Slot(str, float)
    def set_parameter(self, parameter_name: str, value: float):
       
        
        response = self._ion_gun_hardware().set_parameter(parameter_name, value)
        print(response)
        if response != 'Not in Remote mode':

            self.current_values[parameter_name] = value


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

    @Slot()

        
        
        