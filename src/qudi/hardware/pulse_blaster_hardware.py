from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
from qudi.hardware import spinapi
import nidaqmx
import numpy as np
import time



class PulseBlasterHardware(Base):

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        
    def on_activate(self) -> None:
        self.initialise()

    def on_deactivate(self) -> None:
        self.stop_programming()
        self.stop()
        self.close()

    def initialise(self):
        """
        Initialize the Pulse Blaster hardware.
        This function is called when the hardware is activated.
        It sets up the Pulse Blaster and prepares it for programming.
        """
        print("Initialising Pulse Blaster hardware...")
        self.close()
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            raise Exception("Failed to initialize Pulse Blaster")
        spinapi.pb_reset()
        spinapi.pb_core_clock(500)
    
    def start_programming(self):
        """
        Start programming the Pulse Blaster.

        This function initializes the Pulse Blaster, resets it, sets the core clock,
        and starts programming the pulse program. It should be called before any
        programming instructions are sent to the Pulse Blaster.
        It selects the first board (0) and initializes it. If the initialization fails,
        it raises an exception.
        """
        spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

    def get_channel_binary(self, channel: int | list | tuple) -> int:
        """
        Get the binary representation of the channel.

        It converts the channel number(s) to a binary format with
        24 bits, where each bit represents a channel. Channel 0 
        corresponds to the least significant bit, and channel 21
        corresponds to the bit 21. 3 most significant bits are 
        reserved for the pulse blaster short pulse functionality.

        Parameters
        ----------
        channel : int, list or tuple
            The channel number or a list/tuple of channel numbers.
            If an integer is provided, it returns the binary representation of that channel.
            If a list or tuple is provided, it returns the binary representation of all channels combined.
        """
        if type(channel) == int:
            return 1 << channel
        elif type(channel) == list or type(channel) == tuple:
            binary_str = ''.join(map(str, channel[::-1]))  # Reverse the list
            return int(binary_str, 2)
        else:
            return None

    def get_string_representation_from_decimal(self, decimal: int) -> str:
        """
        Get the string representation of the binary state.

        It converts the binary state to a string representation, where each bit
        corresponds to a channel. The string is 24 characters long, with '1' for
        channels that are on and '0' for channels that are off.

        This is meant as an auxiliary function to visualize the state of the channels.
        The string is formatted in groups of 4 bits, separated by spaces. 
        This function is not meant to be used for programming the Pulse Blaster.

        Parameters
        ----------
        binary : int
            The binary state of the channels.

        Returns
        -------
        str
            The string representation of the binary state.
        """
        if decimal < 0 or decimal >= 2**24:
            raise ValueError("Decimal value must be between 0 and 2^24 - 1.")
        formatted = format(decimal, '024b')
        return " ".join([formatted[::-1][i:i+4] for i in range(0, len(formatted), 4)])[::-1]
    
    def program_switch_state(self, channel_state: list | tuple):
        """
        Switch the state of the Pulse Blaster outputs.
        Turns them on or off based on the provided channel state.

        Parameters
        ----------
        channel_state : list or tuple
            A list or tuple of integers representing the channels to be switched on.
            Each integer should be 0 or 1, where 1 means the channel is on and 0 means it is off.
        
        Returns
        -------
        None
        """
        binary_state = spinapi.ON | self.get_channel_binary(channel_state)
        start = spinapi.pb_inst_pbonly(binary_state, spinapi.CONTINUE, 0, 200.0 * spinapi.ms)
        spinapi.pb_inst_pbonly(binary_state, spinapi.BRANCH, start, 200.0 * spinapi.ms)

    def program_looped_variation(self, variation: list, number_of_loops: int):
        """
        Program a looped variation of the Pulse Blaster outputs.

        This function takes a list of variations and the number of loops to be executed.
        Each variation is a list of Pulse objects, and the function generates
        a loop of instructions for the Pulse Blaster.
        [pulse1, pulse2, ...]
        """
        spinapi.pb_close()
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            exit(-1)
        spinapi.pb_reset()
        spinapi.pb_core_clock(500)
        self.start_programming()

        start_pb_loop = spinapi.pb_inst_pbonly(
            spinapi.ON | int(sum(variation[0].channel_binary[0])),
            spinapi.Inst.LOOP,
            number_of_loops,
            (variation[0].end_tail - variation[0].start_tail) * spinapi.ms,
        )

        #print(
        #    f"spinapi.pb_inst_pbonly({sum(variation[0].channel_binary[0])},spinapi.Inst.LOOP,{number_of_loops},({variation[0].end_tail-variation[0].start_tail})*spinapi.ms)"
        #)

        for i in range(1, len(variation)): 

            # we start from one because we already did the 0 index
            print(f'i = {i}')
            if i != len(variation) - 1:
                print(
                    f"spinapi.pb_inst_pbonly({sum(list(variation[i].channel_binary[0]))},spinapi.Inst.CONTINUE,0,({variation[i].end_tail-variation[i].start_tail})*spinapi.ms)"
                )
                spinapi.pb_inst_pbonly(
                    spinapi.ON | int(sum(variation[i].channel_binary[0])),
                    spinapi.Inst.CONTINUE,
                    0,
                    (variation[i].end_tail - variation[i].start_tail)
                    * spinapi.ms,
                )
            else:
                print(
                    f"spinapi.pb_inst_pbonly({sum(list(variation[i].channel_binary[0]))},spinapi.Inst.END_LOOP,start,{variation[i].end_tail-variation[i].start_tail}"
                )
                spinapi.pb_inst_pbonly(
                    spinapi.ON | int(sum(variation[i].channel_binary[0])),
                    spinapi.Inst.END_LOOP,
                    start_pb_loop,
                    (variation[i].end_tail - variation[i].start_tail) * spinapi.ms,
                )

            # This instruction stops the pulse sequence.
            # The duration is set to a very small value
            # to ensure the stop instruction is executed
            # almost immediately.
            spinapi.pb_inst_pbonly(
                int(0), spinapi.Inst.STOP, 0, 0
            )  
            #print(
            #    f"spinapi.pb_inst_pbonly(int(0),spinapi.Inst.STOP,0,0.01*spinapi.ms)"
            #)
            self.stop_programming()
            #print(f"spinapi.pb_stop_programming()")


    def busy_wait_us(self, time_us):
        # Convert microseconds to seconds and add it to the current time
        # This gives us the target end time
        end = time.perf_counter() + time_us / 1_000_000

        # Loop until the current time reaches the end time
        while time.perf_counter() < end:
            pass  # This is a "busy wait" — doing nothing but checking the time

    def start(self):
        """
        Start the Pulse Blaster program.
        """
        spinapi.pb_stop_programming()
        spinapi.pb_start()

    def stop(self):
        """
        Stop the current pb program
        """
        spinapi.pb_stop()

    def stop_programming(self):
        """
        Stop programming the Pulse Blaster.
        Note this does not stop the pulse blaster outputs.
        """
        spinapi.pb_stop_programming()

    def close(self):
        """
        Closes communication with the Pulse Blaster.
        """
        spinapi.pb_close()
