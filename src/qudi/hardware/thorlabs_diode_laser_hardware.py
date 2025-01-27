from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
import nidaqmx
import numpy as np


class ThorlabsLaserHardware(Base):

    power_signal = Signal(float)

    def __init__(self, *args, **kwargs) -> None:
        
        super().__init__(*args, **kwargs)
        self.settings = {
            'device': 'Dev1',
            'port': 'port0',
        }

        self.__power = 10
        self.__on_off_status = False

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    @property
    def power(self) -> float:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                "Dev1/ai0",
                min_val=-10,
                max_val=10
            )
            task.start()
            self.__power = task.read()
        return self.__power
    
    @power.setter
    def power(self, value: float) -> None:
        self.__power = value

        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                "Dev1/ao3",
                min_val=0,
                max_val=10
            )
            task.start()
            task.write(value)
        #self.power_signal.emit(value)

    @property
    def on_off_status(self) -> bool:
        return self.__on_off_status
    
    @on_off_status.setter
    def on_off_status(self, value: bool) -> None:
        self.__on_off_status = value

        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                "Dev1/port0/line8",
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE
            )
            task.start()
            task.write(value)
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                "Dev1/port0/line13",
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE
            )
            task.start()
            task.write(value)


if __name__ == '__main__':
    laser = ThorlabsLaserHardware()
    laser.frequency = 0
    laser.power = 10
    laser.on_off_status = True
    print(laser.frequency, laser.power, laser.on_off_status)