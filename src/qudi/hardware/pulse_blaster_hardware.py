from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
from qudi.hardware import spinapi
import nidaqmx
import numpy as np



class PulseBlasterHardware(Base):

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        
    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def start_pulse_blaster_programming(self):
        """
        Start programming the Pulse Blaster.
        """
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            exit(-1)
        spinapi.pb_reset()
        spinapi.pb_core_clock(500)
        spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

    def get_channel_binary(self, channel: int | list | tuple) -> int:
        """
        Get the binary representation of the channel.
        """
        if type(channel) == int:
            return 1 << channel
        elif type(channel) == list or type(channel) == tuple:
            binary = 0
            for ch in channel:
                binary |= 1 << ch
            return binary
        else:
            return None

    def switch_pb_state(self, channel_state: list | tuple):
        """
        Switch the state of the Pulse Blaster.
        """
        binary_state = spinapi.ON | self.get_channel_binary(channel_state)
        spinapi.pb_inst_pbonly(binary_state, spinapi.BRANCH, 0, 0)

    def start_pulse_blaster(self):
        """
        Start the Pulse Blaster.
        """
        spinapi.pb_stop_programming()
        spinapi.pb_start()

    def stop_pulse_blaster(self):
        """
        Stop the Pulse Blaster.
        """
        spinapi.pb_stop()

    def stop_pulse_blaster_programming(self):
        """
        Stop programming the Pulse Blaster.
        """
        spinapi.pb_stop_programming()

    def close_pulse_blaster(self):
        """
        Close the Pulse Blaster.
        """
        spinapi.pb_close()
