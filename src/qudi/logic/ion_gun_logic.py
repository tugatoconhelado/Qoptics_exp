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
class ImplantationParameters:
    emision_current: float = 10000
    energy: float = 5000
    extractor_voltage: float = 90.01
    focus_1_voltage: float = 75.00
    focus_2_voltage: float = 0.00
    position_x: float = 0
    position_y: float = 0
    width_x: float = 0
    width_y: float = 0
    blanking_x: float = 1
    blanking_y: float = 1
    blanking_level: float = 0
    time_per_dot: float = 50
    angle_phi: float = 0
    angle_theta: float = 0
    L: float = 33000
    M: float = 11500
    deflection_x: float = 48
    deflection_y: float = 67

@dataclasses.dataclass
class ImplantationSpot:
    implantation_time: float = 0
    position_x: float = 0
    position_y: float = 0
    extra_parameter: dict  = {}
    total_parameters: ImplantationParameters = ImplantationParameters()

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
    
    def set_sacrifice_spot(self, pos_x: float, pos_y: float):
        self.sacrifice_spot = (pos_x, pos_y)

class IonGunLogic(LogicBase):
    refresh_ports_signal = Signal(list)
    unlock_connect_signal = Signal()
    lock_connect_signal = Signal()
    update_parameter_signal = Signal(str,str)
    update_parameter_for_setter_signal = Signal(float)
    update_parameter_spot_setter_signal = Signal(float)

    _ion_gun_hardware = Connector(name='ion_gun_hardware',
                                   interface='IonGunHardware'
                                   )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.implantation_matrix = ImplantationMatrix()
        self.current_values = ImplantationParameters()
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
        atribute_parameter = parameter_name.lower().replace(' ','_')
        #Chanche the fisrt letter to upper case
        atribute_parameter = atribute_parameter[0].upper() + atribute_parameter[1:]
        if atribute_parameter[-1] in ['x','y']:
            atribute_parameter = atribute_parameter[:-1] + atribute_parameter[-1].upper()
        
        value = getattr(self.current_values, atribute_parameter)
        self.update_parameter_for_setter_signal.emit(value)
    
    @Slot(str, float)
    def set_parameter(self, parameter_name: str, value: float):
        response = self._ion_gun_hardware().set_parameter(parameter_name, value)
        current_spot_values = self.implantation_matrix.current_implantation_spot.total_parameters
        print(response)
        if response != 'Not in Remote mode':
            setattr(self.current_values, parameter_name.lower().replace(' ','_'), value)
            setattr(current_spot_values, parameter_name.lower().replace(' ','_'), value)

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
    def add_implantation_spot(self, pos_x: float, pos_y: float, implantation_time: float):
        self.implantation_matrix.add_implantation_spot(pos_x, pos_y, implantation_time)
        
    @Slot()
    def remove_implantation_spot(self):
        self.implantation_matrix.remove_implantation_spot()
    
    @Slot(str, float)
    def add_implantation_spot_parameter(self, parameter_name: str, value: float):
        self.implantation_matrix.add_implantation_spot_parameter(parameter_name, value)
        setattr(self.implantation_matrix.current_implantation_spot.total_parameters, parameter_name.lower().replace(' ','_'), value)
    
    @Slot(str)
    def remove_implantation_spot_parameter(self, parameter_name: str):
        self.implantation_matrix.remove_implantation_spot_parameter(parameter_name)
    
    @Slot(float, float)
    def set_sacrifice_spot(self, pos_x: float, pos_y: float):
        self.implantation_matrix.sacrifice_spot(pos_x, pos_y)
    
    @Slot()
    def move_to_sacrice_point(self):
        self._ion_gun_hardware().set_parameter('Position X', self.implantation_matrix.sacrifice_point[0])
        self._ion_gun_hardware().set_parameter('Position Y', self.implantation_matrix.sacrifice_point[1])

    @Slot()
    def get_status(self):
        status = self._ion_gun_hardware().get_status()
        print(status)


    @Slot(str)
    def get_parameter_spot_setter(self, parameter_name: str):
        atribute_parameter = parameter_name.lower().replace(' ','_')
        #Chanche the fisrt letter to upper case
        atribute_parameter = atribute_parameter[0].upper() + atribute_parameter[1:]
        current_spot_values = self.implantation_matrix.current_implantation_spot.total_parameters
        if atribute_parameter[-1] in ['x','y']:
            atribute_parameter = atribute_parameter[:-1] + atribute_parameter[-1].upper()
        
        value = getattr(current_spot_values, atribute_parameter)
        self.update_parameter_spot_setter_signal.emit(value)

    @Slot()
    def start_matrix(self):
        for spot in self.implantation_matrix.implantation_matrix:
            self.move_to_sacrice_point()
            for parameter in spot.extra_parameter.keys():
                self._ion_gun_hardware().set_parameter(parameter, spot.extra_parameter[parameter])
            is_stanby = True
            while is_stanby:
                status = self._ion_gun_hardware().get_status()
                print(status)
                #Check what is the response for get status...
                if status == 'Standby':
                    is_stanby = False
            self._ion_gun_hardware().set_parameter('Position X', spot.position_x)
            self._ion_gun_hardware().set_parameter('Position Y', spot.position_y)

            