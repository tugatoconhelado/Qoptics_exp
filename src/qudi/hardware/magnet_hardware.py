import numpy as np
import nidaqmx
import nidaqmx.stream_writers
import copy
import time
from PySide2.QtCore import Slot, Signal
from PySide2.QtWidgets import QApplication
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
import serial
import serial.tools.list_ports


class MagnetHardware(Base):

    position_changed = Signal(int)
    com_ports_signal = Signal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__current_position = 0
        self.continue_moving = True
        self.controller = None

    def on_activate(self):
        pass
    
    def on_deactivate(self):
        self.disconnect_arduino_controller()

    @Slot(str)
    def initialise_arduino_controller(self, com_port: str):

        try:
            self.controller = serial.Serial(com_port, 9600)
            self.log.info(f'Arduino controller connected in port {com_port}')
        except Exception as e:
            print(e)
    
    @Slot()
    def disconnect_arduino_controller(self):
        if self.controller is not None:
            try:
                self.controller.close()
                self.log.info('Arduino controller disconnected.')
            except Exception as e:
                print(e)

    @Slot()
    def get_com_ports(self):

        ports = serial.tools.list_ports.comports()
        self.com_ports_signal.emit(ports)
        return ports

    @property
    def current_position(self):
        return self.__current_position
    
    @current_position.setter
    def current_position(self, value):
        self.__current_position = value
        self.position_changed.emit(value)


    def move_by_steps(self, steps, direction):

        self.continue_moving = True
        if self.controller is None:
            return
        if direction == 'Forward':
            self.controller.write(f'{steps}\n'.encode())
        elif direction == 'Backward':
            self.controller.write(f'{-steps}\n'.encode())
        response = self.controller.readline()
        time.sleep(0.1)
        self.current_position += steps if direction == 'Forward' else -steps
        #for i in range(steps):
        #    if self.continue_moving:
        #        interval = 0.0001
        #        if direction == 'Forward':
        #            #Retrocede solo si en ambas ocasiones DIR es True

        #            self.controller.write(b'1\n')
        #            self.controller.readline()
        #            self.current_position += 1

        #        else:
        #            self.controller.write(b'-1\n')
        #            self.controller.readline()
        #            self.current_position -= 1
        #    elif not self.continue_moving:
        #        break
        #    QApplication.processEvents()
        
    def go_to_position(self, position):
        
        steps = position - self.current_position
        direction = 'Forward' if steps > 0 else 'Backward'
        self.move_by_steps(abs(steps), direction)

    @Slot()
    def set_position_as_zero(self):
        self.current_position = 0

    def stop_motor(self):
        self.continue_moving = False
