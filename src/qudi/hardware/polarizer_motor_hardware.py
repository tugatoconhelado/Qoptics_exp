from pylablib.devices import Thorlabs
from PySide2.QtWidgets import QApplication
import time
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
import nidaqmx
import numpy as np


class PolarizerMotorHardware(Base):

    position_signal = Signal(float)

    def __init__(self, *args, **kwargs) -> None:
        
        super().__init__(*args, **kwargs)
        self.polarizer_motor = None

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def get_device_list(self) -> list:
        return Thorlabs.kinesis.list_kinesis_devices()
     
    def initialise_motor(self, serial_number: str) -> None:
        self.polarizer_motor = Thorlabs.kinesis.KinesisMotor(serial_number, scale='stage')

    def stop_motor(self) -> None:

        if self.polarizer_motor is not None:
            self.polarizer_motor.stop(immediate=True)

    def move_to(self, position: float) -> None:
        if self.polarizer_motor is not None:
            if self.polarizer_motor.is_moving():
                self.polarizer_motor.stop(immediate=True)
            self.polarizer_motor.move_to(position)
            self.wait_until_stopped()
            return self.polarizer_motor.get_position()

    def move_by(self, distance: float) -> None:
        if self.polarizer_motor is not None:
            if self.polarizer_motor.is_moving():
                self.polarizer_motor.stop(immediate=True)
            self.polarizer_motor.move_by(distance)
            self.wait_until_stopped()
            return self.polarizer_motor.get_position()

    def get_position(self) -> float:
        if self.polarizer_motor is not None:
            return self.polarizer_motor.get_position()
        return None
    
    def wait_until_stopped(self) -> None:
        if self.polarizer_motor is not None:
            while self.polarizer_motor.is_moving():
                self.position_signal.emit(self.polarizer_motor.get_position())
                QApplication.processEvents()
