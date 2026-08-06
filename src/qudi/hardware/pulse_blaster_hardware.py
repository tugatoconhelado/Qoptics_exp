from dataclasses import dataclass
from . import spinapi as spinapi
from qudi.core.module import Base


@dataclass
class Instruction:
    """
    A class to represent PulseBlaster instructions

    Attributes
    ----------
    flags : int
        determines state of each TTL output bit.
    inst : int
        determines which type of instruction is to be executed
    inst_data : int
        data to be used with the previous 'inst' field
    length : int
        duration of the pulse program instruction, specified in ns

    Methods
    -------
    program():
        Programs the instruction onto the currently selected board
    """

    flags: int
    inst: int
    inst_data: int
    length: int

    def __str__(self):
        """
        Convert instruction into a string representation for readability

        Returns
        -------
        str
            formatted string that represents the contents of the instruction
        """

        opcodes = [
            "CONTINUE",
            "STOP",
            "LOOP",
            "END LOOP",
            "JSR",
            "RTS",
            "BRANCH",
            "LONG DELAY",
            "WAIT",
        ]

        return f"{format(self.flags, '#026b')} | {format(opcodes[self.inst], '^10s')} | {self.inst_data} | {self.length} ns"

    def program(self):
        """
        Programs the instruction onto the currently selected board
        """
        self.flags = spinapi.ON | self.flags
        rc = spinapi.pb_inst_pbonly(self.flags, self.inst, self.inst_data, self.length * spinapi.ns)
        if rc < 0:
            raise PulseBlasterError(f"pb_inst failed ({rc}): {spinapi.pb_get_error()}")
        return rc

class PulseBlasterError(Exception):
    """Base exception for PulseBlaster-related errors."""

    pass

class BoardNotFoundError(Exception):
    """Raised when no PulseBlaster board is found."""

    pass

class InvalidChannelError(Exception):
    """Raised when an invalid channel is accessed."""

    pass

class FirmwareMismatchError(Exception):
    """Raised when the firmware is not recognized and user input is invalid."""

    pass


class PulseBlasterHardware(Base):

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        # The ESR-PRO 500 crashes if a state is less than 5 clock cycles (10ns)
        self.min_instruction_ns = 10

        self.running = False  # Flag if board is running (Leave here so exit() function works properly)

    def on_activate(self) -> None:
        self.initialize()

    def on_deactivate(self) -> None:
        self.stop()
        self.close()

    def initialize(self, clock=0):
        print("Initializing new PulseBlaster board.")

        # Display SpinAPI version
        print(f"SpinAPI version: {spinapi.pb_get_version()}")

        board_number = 0  # Default
        board_count = spinapi.pb_count_boards()
        if board_count <= 0:
            raise BoardNotFoundError("No boards found on your system")

        board_number = 0

        if spinapi.pb_select_board(board_number) != 0:
            raise PulseBlasterError(f"Failed to select board: {spinapi.pb_get_error()}")

        if spinapi.pb_init() != 0:
            raise PulseBlasterError(f"Failed to initialize: {spinapi.pb_get_error()}")

        # Set member variables
        self.channels, self.clock, self.memory = self._match_firmware()
        self.board_number = board_number
        self.queues = [[] for _ in range(self.channels)]

        # Check if user has input their own clock frequency
        if clock != 0:
            self.clock = clock

        # Set core clock frequency
        self.reset()
        spinapi.pb_core_clock(self.clock)

        # Print status
        print("Initiated new PulseBlaster board.")

    def start(self):
        """Starts the PulseBlaster board program execution."""
        if spinapi.pb_start() != 0:
            raise PulseBlasterError(
                f"Failed to start PulseBlaster program: {spinapi.pb_get_error()}"
            )
       
        self.running = True

    def reset(self):
        """Resets the PulseBlaster board to beginning of program."""
        if spinapi.pb_reset() != 0:
            raise PulseBlasterError(
                f"Failed to reset PulseBlaster program: {spinapi.pb_get_error()}"
            )
        print("PulseBlaster board has been reset.")
        self.running = True

    def stop(self):
        """Stops the currently running PulseBlaster program."""
        if spinapi.pb_stop() != 0:
            raise PulseBlasterError(
                f"Failed to stop PulseBlaster program: {spinapi.pb_get_error()}"
            )

        self.running = False

    def close(self):
        """
        Closes communication with the Pulse Blaster.
        """
        spinapi.pb_close()

    def program(self, instructions: list):
        """Programs the PulseBlaster board with a list of instructions.

        This sends the instruction queue to the hardware and clears the queue.
        """
        # Validate number of instructions
        if len(instructions) > self.memory:
            print("Warning: Too many instructions")

        self.stop()
        if spinapi.pb_start_programming(spinapi.PULSE_PROGRAM) != 0:
            print("something happened!!!!")
            raise PulseBlasterError(
                f"Failed to start programming PulseBlaster program: {spinapi.pb_get_error()}"
            )
        print("started programming board")

        for instr in instructions:
            ref = instr.program()
            print(f"Instruction {instr} | Reference {ref}")
        
        if spinapi.pb_stop_programming() != 0:
            print("something happened!!!!")
            raise PulseBlasterError(
                f"Failed to stop programming PulseBlaster program: {spinapi.pb_get_error()}"
            )
        print("stopped programming board")

    def compile(self, sequence, loop=None, branch=None) -> list:
        """Converts a Sequence into a list of PulseBlaster instructions."""

        # Find all unique edges (events) in the timeline
        edges = set([0])  # Always start at t=0
        for channel in sequence.channels.values():
            for pulse in channel.pulses:
                edges.add(pulse.start)
                edges.add(pulse.end)

        sorted_edges: list[int] = sorted(list(edges))

        instructions: list[Instruction] = []

        # Iterate through time slices
        for i in range(len(sorted_edges) - 1):
            t_start: int = sorted_edges[i]
            t_end: int = sorted_edges[i + 1]
            dt: int = t_end - t_start

            # Determine bitmask for this slice
            flags = 0
            for channel in sequence.channels.values():
                for pulse in channel.pulses:
                    # If this pulse covers the current time slice:
                    if pulse.start <= t_start and pulse.end >= t_end:
                        flags |= 1 << channel.pb_id  # Flip the bit to 1!
                        break  # We found a pulse for this channel, move to next channel

            # Enforce hardware constraints
            if dt < self.min_instruction_ns:
                raise ValueError(
                    f"Hardware constraint violated: Time slice at {t_start}ns is "
                    f"only {dt}ns long (Minimum is {self.min_instruction_ns}ns)."
                )

            instructions.append(
                Instruction(
                    flags=flags,
                    inst=spinapi.CONTINUE,
                    inst_data=0,
                    length=dt,
                )
            )

        if loop is not None:
            loop_start = instructions[0]
            loop_start.inst = spinapi.LOOP
            loop_start.inst_data = loop

            loop_end = instructions[-1]
            loop_end.inst = spinapi.END_LOOP
            loop_end.inst_data = 0 # The loop start instruction, which in this case is always 0

        elif branch is not None:
            branch_start = instructions[branch]
            final_instr = instructions[-1]
            final_instr.inst = spinapi.BRANCH
            final_instr.inst_data = branch

        if branch is None:
            stop_instr = Instruction(0, spinapi.STOP, 0, 100)
            instructions.append(stop_instr)

        return instructions

    def switch_state(self, channel_state: list or tuple):
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
        print("Switching state")
        # Get the binary representation of the channel
        binary_str = ''.join(map(str, channel_state[::-1])) 
        channel_binary = int(binary_str, 2)

        # Aplly states
        binary_state = spinapi.ON | channel_binary
        start_instr = Instruction(binary_state, spinapi.CONTINUE, 0, 200)
        end_instr = Instruction(binary_state, spinapi.BRANCH, 0, 200)
        self.program([start_instr, end_instr])
        self.start()

    def _match_firmware(self):
        """Determines board specifications based on the firmware ID.

        Returns
        -------
        tuple 
            A tuple of (channels, clock frequency, memory) depending on the board firmware.
        """
        return (21, 500.0, 4096)