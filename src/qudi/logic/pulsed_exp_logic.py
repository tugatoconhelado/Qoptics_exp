import numpy as np
from PySide2.QtCore import Signal, Slot, QTimer, QObject
from PySide2.QtWidgets import QApplication
import os
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
import pyqtgraph as pg
import datetime
from qudi.hardware import spinapi
import nidaqmx
import time
import json

import dataclasses

@dataclasses.dataclass
class PulseData:

    iteration_range: list
    channel_tag: int = 0
    start_time: int = 1000
    width: float = 0.1
    function_start: str = ""
    function_width: str = ""
    

@dataclasses.dataclass
class ChannelData:

    delay: list
    tag: int = 0
    channel_type: str = ""


@dataclasses.dataclass
class SequenceData:

    channels: list
    pulses: list

@dataclasses.dataclass
class PulsedExpParameterData:

    sequence: str
    iterations: int = 30
    repeat_exp: int = 10
    loop: int = 10_000

@dataclasses.dataclass
class PulsedExpData:

    parameters: PulsedExpParameterData
    tau: np.ndarray
    pl_raw_mean: np.ndarray
    pl_raw_std: np.ndarray
    pl_mean: np.ndarray
    pl_std: np.ndarray

class PulsedExpLogic(LogicBase):
    """ Logic measurement module for pulsed experiments using PulseBlaster.

    Config that goes into the config file:

    pulsed_exp_logic:
      module.Class: pulsed_exp_logic.PulsedExpLogic
      options: {}
      connect:
        pulse_blaster_hardware: pulse_blaster_hardware
        apd_hardware: apd_hardware
        tracking_logic: tracking_logic
      allow_remote: false

    Methods
    -------
    """

    status_msg = Signal(str)
    adding_channel_to_list = Signal(
        int, int, int, str
    ) 
    frame_data_signal = Signal(list, list, int, int)
    next_frame_signal = Signal(int)
    add_iteration_txt = Signal(str)
    added_pulse_signal = Signal(int, float, float, str, str, int, int)
    error_str_signal = Signal(str)
    data_signal = Signal(np.ndarray, np.ndarray, np.ndarray)
    file_changed_signal = Signal(str)

    # Declare static parameters that can/must be declared in the qudi configuration
    # _increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _pulse_blaster_hardware = Connector(
        name="pulse_blaster_hardware", interface="PulseBlasterHardware", optional=True
    )
    _apd_hardware = Connector(
        name="apd_hardware", interface="APDHardware", optional=True
    )
    _tracking_logic = Connector(
        name="tracking_logic", interface="TrackingLogic", optional=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        self.measure = False
        self.track_intensity = False

        self.time_counter = 0
        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, "c:" + os.sep, "EXP", "data"),
            experiment_name="pulsed_exp",
            exp_str="PEXP",
        )

        self.added_channel_tags = ([])  
        self.channels = []  
        self.experiment_hub = []  
        self.Max_end_time = 0  # It gives you the max end time of all iterations
        self.max_variations = 0
        
        self.added_channels = []  # list of the channels that are added to the database
        self.added_pulses = []  # list of the pulses that are added to the database
        self.continue_experiment = False

        self.LIST_OF_CHANNEL_LABELS = [
            "green",
            "yellow",
            "red",
            "apd",
            "microwave",
            "blue",
            "pink",
            "orange",
        ]
        self.TOTAL_CHANNELS = 21

    def on_activate(self):
        
        parameters = PulsedExpParameterData(
            [],
            30,
            10,
            10000
        )
        self.data = PulsedExpData(
            parameters,
            np.zeros(10),
            np.zeros(10),
            np.zeros(10),
            np.zeros(10),
            np.zeros(10)
        )

    def on_deactivate(self):
        pass

    @Slot(int, list, str, int)
    def add_channel(
        self, channel_tag, channel_delay, channel_label, channel_count
    ):
        """
        Adds a channel to the database.
        """
        # Logic to add a channel to the database
        channel_tag = int(channel_tag)
        flag = [channel_tag, channel_delay, channel_label]

        if channel_tag not in self.added_channel_tags:
            # This is for the Graphs in the Sequence Plot
            if channel_label in self.LIST_OF_CHANNEL_LABELS:
                flag_str = f"channel: {flag[0]}, delay_on: {abs(flag[1][0])}, delay_off: {abs(flag[1][1])}, {flag[2]}"
                status_str = "Adding " + flag_str
                self.status_msg.emit(status_str)

                self.adding_channel_to_list.emit(
                    channel_tag, channel_delay[0], channel_delay[1], channel_label
                )
                channel_binary = self.convert_to_binary(
                    channel_tag, channel_count
) 
                self.added_channel_tags.append(flag[0])  # add channel to the set
                channel = Channel(
                    channel_tag, channel_binary, channel_label, channel_delay
                )
                self.channels.append(channel)
                self.added_channels.append(
                    ChannelData(
                        tag=channel_tag, channel_type=channel_label, delay=channel_delay
                )
                )
                self.channels = sorted(
                    self.channels, key=lambda ch: ch.tag
                )
                print(f"channel color: {channel.label}")

            else:
                self.error_str_signal.emit(
                    f"Label {channel_label} not recognized. Please use one of the following: green, yellow, red, apd, microwave"
                )
        else:
            self.error_str_signal.emit(f"Channel {channel_tag} already added")
        return flag

    @Slot(list)
    def modify_channels(self, modified_channels: list):
        """
        Modify the channel in the database.
        """
        # Logic to modify a channel in the database
        found = False
        current_pulses = self.added_pulses
        self.clear_channels()
        for channel in modified_channels:
            tag = channel[0]
            delay = channel[1]
            label = channel[2]
            self.add_channel(tag, delay, label, self.TOTAL_CHANNELS)
        # Add the pulses to the channels
        for pulse in current_pulses:
            self.add_pulse_to_channel(
                pulse.start_time,
                pulse.width,
                pulse.function_width,
                pulse.function_start,
                pulse.iteration_range,
                pulse.channel_tag,
            )

    @Slot(list)
    def modify_pulses(self, pulses_data: list):
        """
        Modify a pulse in the database

        In order to easily modify the pulses, the software deletes 
        and creates again all the pulses already added.

        Parameters
        ----------
        pulses_data : list
            Data of all the pulses that should be in the database,
            this contains any modifications done to the pulses.
            Each list element is a list of the form:
            [channel_tag, start_time, width, function_width, function_start, iteration_range]
        """
        # Delete all pulses
        for channel in self.channels:
            channel.clear_all_pulses()
        self.added_pulses = []  # Clear the list of added pulses
        # Add all pulses again
        for pulse_data in pulses_data:
            channel_tag = pulse_data[0]
            start_time = pulse_data[1]
            width = pulse_data[2]
            function_width = pulse_data[3]
            function_start = pulse_data[4]
            iteration_range = pulse_data[5]
            self.add_pulse_to_channel(
                start_time,
                width,
                function_width,
                function_start,
                iteration_range,
                channel_tag,
            )

    def convert_to_binary(self, channel_tag, channel_count):
        """We need to conver the channel tag index into a binary number for the pulse blaster
        it's better to do this now than later because, later would require for loops on the experiments methods
        and it will be inneficient.

        Given the total number of channels and a target channel_tag (index),
        return the decimal value corresponding to only that channel being activated.

        Args:
            channel_count (int): Total number of channels (length of the bitmask).
            channel_tag (int): Index of the channel to activate (0-based).

        Returns:
            int: Decimal value of the binary number with only channel_tag set to 1.
        """
        if channel_tag >= channel_count or channel_tag < 0:
            raise ValueError(
                "channel_tag must be within the range of available channels."
            )

        binary = [0] * channel_count
        binary[-(channel_tag + 1)] = 1  # Activate the correct bit from the right
        binary_str = "".join(map(str, binary))
        decimal = int(binary_str, 2)
        return decimal

    def add_pulse_to_channel(
        self,
        start_time,
        width,
        function_width,
        function_start,
        iteration_range,
        channel_tag,
    ):
        """here we check if we got a channel to add the pulse, then we call a method of the channels class, that creates a sequence per iteration."""
        if (
            self.max_variations < iteration_range[1]
        ):  # meaning we have new bigger variation
            self.max_variations = iteration_range[1]
        # check if we got a channel to add the pulse
        if len(self.channels) == 0:
            self.error_str_signal.emit("No channels added")
            return
        elif channel_tag not in self.added_channel_tags:
            self.error_str_signal.emit(f"Channel {channel_tag} not added")

        elif channel_tag in self.added_channel_tags:
            for channel in self.channels:
                if channel.tag == channel_tag:
                    max_end_time_added_sequence, added_pulse = channel.a_sequence(
                        start_time,
                        width,
                        function_width,
                        function_start,
                        iteration_range,
                    )
                    channel.error_adding_pulse_channel.connect(
                        self.error_str_signal.emit
                    )
                    break
            if max_end_time_added_sequence > self.Max_end_time:
                self.Max_end_time = max_end_time_added_sequence
            print(f"added_pulse: {added_pulse}")
            if added_pulse is True:
                self.added_pulse_signal.emit(
                    channel_tag,
                    start_time,
                    width,
                    function_width,
                    function_start,
                    iteration_range[0],
                    iteration_range[1],
                )
                print(f"Added pulse to channel {channel_tag}")
                self.added_pulses.append(
                    PulseData(
                        channel_tag=channel_tag,
                        start_time=start_time,
                        width=width,
                        function_start=function_start,
                        function_width=function_width,
                        iteration_range=iteration_range,
                    )
                )
        print(f"self.Max_end_time:{self.Max_end_time}")

    @Slot(int, int, int, dict, str)
    def run_experiment(self, value_loop: int, loop_type: int, repeat_exp: int = 1, track_options: dict = None, sequence: str = "T1"):
        """
        Starts the pulsed experiment.

        Here we iterate through each iteration of the loop to find the channels that have a sequence for that iteration
        then we order the pulses from the channels that have pulses in this iteration. Then we create an object from the
        class experiment. which we then add to our list Experiment_Hub. Finally, the APD is configured if a channel with
        label "apd" exists. The experiment is then executed based on the specified loop type (A or B).

        Parameters
        ----------
        value_loop : int
            Number of times x each variation or all variations are looped, depending on the loop type.
        loop_type : int
            Type of loop to use (0 for variation loop, 1 for all variations loop).
        repeat_exp : int, optional
            Number of times j to repeat the entire experiment, by default 1.
        """
        list_type_cero = []
        max_end_times_vars = []  # max end times per variation
        for i in range(1, self.max_variations + 1):
            Exp_i_pb = []
            max_end = 0
            for channel in self.channels:
                result = channel.a_experiment(i) # Returns [pulse, end_time]
                list_channel_sequence = result[0]
                if list_channel_sequence != None:
                    Exp_i_pb.append(list_channel_sequence)
                    if max_end < result[1]:
                        max_end = result[1] # max end time of the variation
            max_end_times_vars.append(max_end)
            exp = Experiment(Exp_i_pb, i) 
            # order the pulses of all the channels by time
            # in the instace of the variation of the experiment 
            exp.Prepare_Exp() 

            self.experiment_hub.append(exp) 
            list_type_cero.append(exp.pb_sequence)

        self.apd_is_gated = False
        self.continue_experiment = True
        chunck_separation = value_loop
        divide_exp = self.divide_loops_into_chunks(
            loops=value_loop, separation=chunck_separation, max_separation=1_000_000
        )

        det_pulses = 0
        for channel in self.channels:
            if channel.label == "apd":
                self.apd_is_gated = True
                det_pulses += len(channel.added_pulses)
                self.time_function = channel.added_pulses[0].function_start

        self.pl_data = np.zeros((repeat_exp, self.max_variations))
        self.pl_std = np.zeros((repeat_exp, self.max_variations))
        self.data.pl_raw_mean = np.zeros((repeat_exp, self.max_variations, det_pulses))
        self.data.pl_raw_std = np.zeros((repeat_exp, self.max_variations, det_pulses))
        self.data.parameters.iterations = self.max_variations
        self.data.parameters.loop = sum(divide_exp)
        self.data.parameters.repeat_exp = repeat_exp
        self.data.parameters.sequence = sequence
        print(f'Number of apd pulses: {det_pulses}')

        if loop_type == 0:
            """
            Variation loop_type A: Loop each variation x times individually
            (v1), (v1), ..., (v1), (v2), (v2), ..., (v2), (v3), (v3), ..., (v3)
            Each variation is looped x times
            """
            self.run_sequence_type_a(
                list_type_cero,
                repeat_exp,
                max_end_times_vars,
                divide_exp,
                det_pulses,
                track_options
            )

        elif loop_type == 1:
            """
            Variation loop_type B: Loop all variations consecutively
            (v1, v2, v3), (v1, v2, v3), (v1, v2, v3), ... x times
            """
            self.run_sequence_type_b(
                list_type_cero, repeat_exp, max_end_times_vars, divide_exp
            )

        else:
            self.error_str_signal.emit(
                f"Loop type {loop_type} not recognized. Please use 0 or 1."
            )
            return
    
    def run_sequence_type_a(self, Flat_exp, repeat_exp, max_end_times_vars, divided_value, det_pulses, track_options=None):

        """here we must iterate each variation a number of value_loop times. we do this for all variations so.
        However to the pulse blaster can only have about 40k instructions and the loop can only iterate a
         maximum of 1 million times. so to get around this  we divide the value_loop by 10k iterations of the experiment

        Parameters
        ----------
        track_options : dict, optional
            Options for tracking intensity during the experiment, by default None.
            Format: {'track': bool, 'by_repetition': bool, 'interval': int}
        """
        #print("sending to pulse blaster")
        #print(f"len(Flat_exp):{len(Flat_exp)}")
        #print(f"divided_value:{divided_value}")
        #print(f"max_end_times_vars:{max_end_times_vars}")
        #print(f"flat_exp:{Flat_exp}")
        #print(f"value_loop:{value_loop}")
        #print(f"counter:{counter}")
        print(f'Max variations: {self.max_variations}')

        spinapi.pb_close()
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            exit(-1)
        spinapi.pb_core_clock(500)
        spinapi.pb_reset()
        #spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

        
        for j in range(0, repeat_exp):
            #print(f"Running experiment iteration {j + 1} of {repeat_exp}")
            if not self.continue_experiment:
                break
            experiment_start = time.perf_counter()
            accumulated_pl = np.zeros(self.max_variations)

            if self.apd_is_gated:
                counter_task = self._apd_hardware().set_gated_apd(
                    samples= det_pulses * sum(divided_value) * self.max_variations,
                )
                self._apd_hardware().start_apd(start_clock=False)

            pl_level = 0

            for i in range(0, self.max_variations):
                """
                For each iteration i (a variation) ,
                we will send one set of instructions 
                to the pulse blaster
                """         
                fluorescence = np.zeros((sum(divided_value), det_pulses))
                for d in range(0, len(divided_value)):

                    # In case the x amount of loops is greater than 10k
                    # the x is divided in steps of 10k
                    value_loop = divided_value[d]
                    #print(f'value_loop={value_loop}')

                    self._pulse_blaster_hardware().program_looped_variation(
                        Flat_exp[i],
                        value_loop
                    )
                    
                    time_wait = max_end_times_vars[i] * value_loop # in ns
                    self._pulse_blaster_hardware().start()

                    if self.apd_is_gated:
                        
                        readed_counts = self._apd_hardware().get_fluorescence(
                            samples= det_pulses * int(value_loop),
                            frequency=1,
                            time_out=time_wait / 1e9 + 1
                        )
                        counts = np.diff(readed_counts)
                        # Add the 0 datum, because diff returns len - 1
                        # Acoounting for fluorescence level of last reading
                        counts = np.append(readed_counts[0] - pl_level, counts)
                        pl_level = readed_counts[-1]

                        # In order to process sequences with multiple apd
                        # pulses, the extracted counts have to be divided
                        # every det_pulses datums
                        det_signals = np.zeros((value_loop, det_pulses))
                        for idx_det in range(det_pulses):
                            det_signals[:, idx_det] = counts[
                                idx_det::det_pulses
                            ]

                        if d != 0:
                            fluorescence[
                                sum(divided_value[0:d])
                                :sum(divided_value[0:d + 1]), :
                            ] = det_signals[:, :]
                        else:
                            fluorescence[0:divided_value[d], :] = det_signals[:, :]
                        
                    elif not self.apd_is_gated:
                        self.busy_wait_us(time_wait / 1000)

                    self._pulse_blaster_hardware().stop()

                    QApplication.processEvents()

                # Since the counts were diffed, now we avg them
                # Each element here has det_pulses elements
                self.data.pl_raw_mean[j, i] = np.average(fluorescence, axis=0)
                self.data.pl_raw_std[j, i] = np.std(fluorescence, axis=0)
            
                processed_data, data_error = self.process_detector_data(fluorescence)
                self.pl_data[j, i] = processed_data
                self.pl_std[j, i] = data_error / np.sqrt(np.sum(divided_value))

                # The factor (repeat_exp / (j + 1)) normalizes
                # the data between repetitions
                column_sums = np.sum(self.pl_data, axis=0)
                std_sums = np.sum(self.pl_std, axis=0)
                ocurrences = np.full(self.pl_data.shape[1], j)
                ocurrences[:i + 1] += 1
                divisor = np.where(ocurrences > 0, ocurrences, 1)
                data_avg = column_sums / divisor
                data_std = std_sums / divisor
                #data_std = np.std(self.pl_data[:j + 1, :], axis=0)
                x_data = np.linspace(1, self.max_variations, self.max_variations)
                time_data = eval(self.time_function, {"S": 6300, "i": x_data})
                time_data = time_data / 1e3 # In us

                self.data.pl_mean = data_avg
                self.data.pl_std = data_std
                self.data.tau = time_data
                self.data_signal.emit(time_data, data_avg, data_std)
                
                if not self.continue_experiment:
                    break
                
            if self.apd_is_gated:
                self._apd_hardware().stop_acquisition()
                self._apd_hardware().stop()

            experiment_end = time.perf_counter()
            print(
                f"Total time for all variations in experiment iteration {j + 1} of {repeat_exp}: {(experiment_end - experiment_start) * 1000:.2f} ms"
            )
            if track_options['track']:
                if (j + 1) % track_options['interval'] == 0:
                    self.switch_pb_outputs((0, 1, 0, 0, 0, 0)) # Turns on green (imaging) laser
                    self.status_msg.emit(f"Tracking intensity at repetition {j + 1}")
                    self.log.info(f"Tracking intensity at repetition {j + 1}")
                    self._tracking_logic().handle_max_request('xyz')
                    self.stop_pb_outputs()
                    self.status_msg.emit("Resuming experiment")
                    self.log.info("Resuming experiment after tracking")
        self.status_msg.emit("Pulsed Experiment finished, stopping pulse blaster and apd hardware")
        self.log.info("Pulsed Experiment finished, stopping pulse blaster and apd hardware")
        self.stop_experiment()

    def process_detector_data(self, det_signals: np.ndarray):

        if det_signals.shape[1] == 2:
            N = det_signals.shape[0]
            avg = np.average(det_signals, axis=0)
            d2 = np.abs(det_signals[:, :] - avg) ** 2
            std = np.sqrt(d2.sum(axis=0) / (N - 1))
            
            num = avg[0]
            den = avg[1]
            num_std = std[0]
            den_std = std[1]
            if den == 0:
                processed_signal = np.nan
                error = np.nan
            else:
                processed_signal = num / den
                error = num / den * np.sqrt((num_std / num) ** 2 + (den_std / den) ** 2)
        elif det_signals.shape[1] == 1:
            processed_signal = np.average(det_signals[:, 0])
            error = np.std(det_signals[:, 0])
        return processed_signal, error

    def run_sequence_type_b(self, Flat_exp, value_loop, max_end_times_vars, divided_value):

        self._pulse_blaster_hardware().start_programming()
        # Exp has structure [[pulse1, pulse2, ...], [pulse1, pulse2, ...]]
        # where [[variation1], [variation2], ...]

        for d in range(0, len(divided_value)):

            # In case the x amount of loops is greater than 10k
            # the x is divided in steps of 10k
            #print(f'Starting loop x={d}')
            value_loop = divided_value[d]
            #print(f'value_loop={value_loop}')
            for loop in range(0, value_loop):
                for j in range(0, self.max_variations):
                    """
                    For each iteration j (a variation) , we will send one set of instructions to the pulse blaster
                    """
                    #print(f"Starting the {j}th variation")
                    self._pulse_blaster_hardware().program_looped_variation(
                        Flat_exp[j],
                        1
                    )
                    self._pulse_blaster_hardware().start()
                    start = time.perf_counter()
                    time_wait = time_wait = max_end_times_vars[j] * 1000
                    #print(f"time_wait:{time_wait}")
                    self.busy_wait_us(
                        time_wait
                    )  # Intended wait: minimum wait time until the next variation
                    end = time.perf_counter()
                    #print(
                    #    f"Actual wait: {(end - start)*1e6:.2f} µs"
                    #)  # to get a glimpse of the error in wait time
                    # el el timepo total que espera el counter para seguir a la siguient variacion. Durante ese tiempo se toman todo los datos de una variacion. Aqui se debe calcular el maximo tiempo de cada variacion y multiplicar por value _loop
                    #print(f"number_of_loops:{number_of_loops}")
                    self._pulse_blaster_hardware().stop()

    def busy_wait_us(self, us):
        # Convert microseconds to seconds and add it to the current time
        # This gives us the target end time
        end = time.perf_counter() + us / 1_000_000

        # Loop until the current time reaches the end time
        while time.perf_counter() < end:
            pass  # This is a "busy wait" — doing nothing but checking the time

    def divide_iter_experiment(self, value_loop):
        """
        here we divide the iterations of th
        """
        #### here we divide the iterations of each varaitions by parts of 10k
        divided_value = []
        if value_loop <= 1_000_000:
            divided_value = [value_loop]  # we only repeat the big loop once
        elif value_loop > 1_000_000:
            difference = 0
            dv = value_loop // 1_000_000  # this gives us the integer result of the fraction
            difference = value_loop - dv * 1_000_000
            if difference > 0:
                length_list = dv + 1
            for h in range(0, length_list):
                if h < length_list - 1:
                    divided_value.append(1_000_000)
                else:
                    divided_value.append(difference)
        print(f"divided_value={divided_value}")
        return divided_value

        # To recieve the counts from the apd

    def divide_loops_into_chunks(self, loops, separation, max_separation):
        """
        Separates the number of loops into chunks based on the desired separation and maximum separation.
        Such that, if the separation is larger than the max_separation, it will use the max_separation, 
        and the next chunk will be the remaining separation, then for the next chunk
        it will again use the max_separation if the remaining separation is still larger than max_separation,
        and the next chunk will be the remaining separation.
        This will continue until the loops are fully divided.

        So, for example, for 100, a separation of 30 and a max_separation of 20,
        it would return [20, 10, 20, 10, 20, 10, 10]

        Parameters
        ----------
        loops : int
            Total number of loops to be divided.
        separation : int
            Desired separation between chunks.
        max_separation : int
            Maximum allowed separation for each chunk.
        """
        chunks = []
        remaining_separation = separation
        while loops > 0:
            if remaining_separation > max_separation:
                chunk = max_separation
            else:
                chunk = remaining_separation
            if chunk > loops:
                chunk = loops
            chunks.append(chunk)
            loops -= chunk
            remaining_separation -= chunk
            if remaining_separation <= 0:
                remaining_separation = separation
        print("Divided loops into chunks:", chunks)
        return chunks

    @Slot()
    def stop_experiment(self):
        """
        This function is used to stop the experiment and close the pulse blaster
        and the apd hardware.
        """
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().stop()
        self._pulse_blaster_hardware().close()  
        self._apd_hardware().stop()
        self.continue_experiment = False

    def prepare_frame(self, frame_i):
        """Each time we change the value of the frame, it shows the corresponding frame in the graph
        for this we need to first identify and obtain the pulses of channes who have a sequence
        for that iterations"""
        sequences_all_channels = []
        tags_colors = []
        for channel in self.channels:
            pulses_channel = channel.a_display(frame_i)

            if pulses_channel != None:  
                sequences_all_channels.append(pulses_channel)
                tags_colors.append([channel.tag, channel.label])
                
        self.frame_data_signal.emit(
            tags_colors, sequences_all_channels, frame_i, self.Max_end_time
        )
 
    def Run_Simulation(self, initial_frame, value_loop, ms_value):
        """
        Starts or stops the simulation when the button is clicked.
        """
        # Check if the timer is already running Use hasattr(self, 'timer') to ensure the self.timer attribute exists before calling isActive().
        if hasattr(self, "timer") and self.timer.isActive():
            # Stop the timer if it's running
            self.timer.stop()
            self.iteration = initial_frame  # Reset the iteration counter
            print("Simulation stopped.")
        else:
            """The timeout signal of QTimer does not pass any arguments
            when it is emitted. However, the update_simulation method
              requires two arguments: initial_frame and value_loop.
              To bridge this gap, a lambda function is used to wrap
              the call to update_simulation and provide the required
                arguments.The lambda creates an anonymous function that
                  calls self.update_simulation(initial_frame, value_loop)
                  whenever the timeout signal is emitted.

            """
            # Initialize iteration counter
            self.iteration = initial_frame  # Current iteration
            # Set up a timer to update the plot
            self.timer = QTimer()
            self.timer.timeout.connect(
                lambda: self.update_simulation(initial_frame, value_loop)
            )
            self.timer.start(ms_value)  # Update at the specified interval
            print("Simulation started.")

    def update_simulation(self, initial_frame, value_loop):

        if self.iteration < value_loop:
            self.iteration = (
                self.iteration + 1
            )  # we add one to the the iteration of the dinamic graph
            self.next_frame_signal.emit(self.iteration)
            self.add_iteration_txt.emit(f"current iteration: ({self.iteration})")
        else:
            self.timer.stop()

            self.iteration = initial_frame
            print("Simulation Stopped")
            self.next_frame_signal.emit(self.iteration)
            self.add_iteration_txt.emit(f"current iteration: ()")

    def clear_channels(self):

        self.added_channel_tags = []
        self.added_channels = []
        self.added_pulses = []
        self.channels = []
        self.experiment_hub = []
        self.Max_end_time = 0

    @Slot(tuple)
    def switch_pb_outputs(self, pb_status: tuple):
        """
        This function is used to switch the outputs of the pulse blaster
        """
        print(f'Switching pulse blaster outputs to {pb_status}')
        self._pulse_blaster_hardware().initialise()
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().stop()
        self._pulse_blaster_hardware().start_programming()
        self._pulse_blaster_hardware().program_switch_state(pb_status)
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().start()
        #print(f'Switching pulse blaster outputs to {pb_status}')

    @Slot()
    def stop_pb_outputs(self):
        """
        This function is used to stop the outputs of the pulse blaster
        """
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().stop()
        print('Stopping pulse blaster outputs')

    def send_data(self, data):

        x_data = np.linspace(1, data.parameters.iterations, data.parameters.iterations)
        self.data_signal.emit(x_data, data.pl_mean, data.pl_std)

    def load_seq_file(self, file_path):
        """
        This function is used to load a file
        """
        print(f"Loading file: {file_path}")
        # Logic to load the file

        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            for channel_data in data["channels"]:
                channel = ChannelData(
                    tag=channel_data["tag"],
                    channel_type=channel_data["channel_type"],
                    delay=channel_data["delay"],
                )
                self.add_channel(channel.tag, channel.delay, channel.channel_type, 21)
            for pulse_data in data["pulses"]:
                pulse = PulseData(
                    channel_tag=pulse_data["channel_tag"],
                    start_time=pulse_data["start_time"],
                    width=pulse_data["width"],
                    function_start=pulse_data["function_start"],
                    function_width=pulse_data["function_width"],
                    iteration_range=pulse_data["iteration_range"],
                )
                self.add_pulse_to_channel(
                    pulse.start_time,
                    pulse.width,
                    pulse.function_width,
                    pulse.function_start,
                    pulse.iteration_range,
                    pulse.channel_tag,
                )

    def save_seq_file(self, file_path):
        """
        This function is used to save a file
        """
        print(f"Saving file: {file_path}")
        data = {
            "channels": [],
            "pulses": []
        }

        # Logic to save the file
        for channel in self.added_channels:
            channel_data_dict = dataclasses.asdict(channel)
            data["channels"].append(channel_data_dict)
        for pulse in self.added_pulses:
            pulse_data_dict = dataclasses.asdict(pulse)
            data["pulses"].append(pulse_data_dict)
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

    @Slot()
    def save_data(self) -> None:
        """
        Saves the data to a file.

        Parameters
        ----------
        filepath : str
            Path to the file where the data will be saved
        """
        data_dict = dataclasses.asdict(self.data)
        data_dict.pop('parameters')
        filepath = self.filemanager.save(
            data=data_dict,
            metadata=dataclasses.asdict(self.data.parameters)
        )
        self.log.info(f'Saved data to {filepath}')
        self.file_changed_signal.emit(filepath)
        return filepath

    @Slot()
    def save_data_as(self):
        """
        Opens a file dialog to save the data to a file.
        """
        data_dict = dataclasses.asdict(self.data)
        data_dict.pop('parameters')
        filepath = self.filemanager.save_as(
            data=data_dict,
            metadata=dataclasses.asdict(self.data.parameters)
        )
        self.log.info(f'Saved data to {filepath}')
        self.file_changed_signal.emit(filepath)
        return filepath

    @Slot()
    def load_data(self):

        data, metadata, general, filepath = self.filemanager.load()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.send_data(self.data)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath

    @Slot()
    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.send_data(self.data)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath

    @Slot()
    def load_next_data(self):

        data, metadata, general, filepath = self.filemanager.load_next()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.send_data(self.data)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    @Slot()
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')


class Channel(QObject):

    def __init__(self, tag: int, binary: int, label: str, delay: list or tuple):
        super().__init__()  # Call the base class's __init__ method
        # for each channel
        self.tag = tag  # the channel tag (ex: PB0, PB1, etc)
        self.label = label
        self.delay = delay
        self.Sequence_hub = []  # in this list we keep all the sequences created
        self.error_flag = False  # Flag to track if an error occurred
        self.binary = binary
        self.added_pulses = []  # list of pulses added to the channel

    error_adding_pulse_channel = Signal(str)

    def clear_all_pulses(self):
        """
        This function is used to clear all the pulses in the channel
        """
        self.Sequence_hub = []
        self.added_pulses = []

    def a_sequence(
        self, start_time, width, function_width, function_start, iteration_range
    ):
        max_end_time = 0
        """
        First we check if the pulse can exist, then we need to check if the user wants to add or edit a pulse, 
        then we add the pulses to the sequences and fuse pulses if needed. Finally we sort the whole self.Sequence_hub
        by order of iteration. 
        """
        #### Checking for errors####
        if self.delay[1] >= width:

            self.error_adding_pulse_channel.emit(
                f"Pulse delay_off={self.delay[1]}>{width}=width"
            )
            return None, None

        start_time_pb = start_time - self.delay[0]

        if start_time_pb < 0:
            self.error_adding_pulse_channel.emit(
                f"Pulse starts with negative time{start_time_pb}"
            )
            return None, None
        ############################

        """ here we need to make for example if iter 
            range [50,55] --> [1,2,3,4,5,6] to plug it into 
            the function for the new width
        """
        self.added_pulses.append(
            PulseData(
                channel_tag=self.tag,
                start_time=start_time,
                width=width,
                function_start=function_start,
                function_width=function_width,
                iteration_range=iteration_range,
            )
        )

        for k in range(iteration_range[0], iteration_range[1] + 1):  
            # we iterate through the iteration range, 
            # +1 for it to include the [50,55] last bracket term

            #print(f"iteration_channel_class: {k}")

            """ now we need to calculate the width of the pulse, by plugging the initial width and the current 
            iteration on the function."""

            # parameter to be replaced in the function
            """generator expression: enumerate provides both the index and the element while iterating throught the list. next() efficiently 
                finds the first match without iterating through the entire list"""
            index = next(
                (
                    j
                    for j, sequence in enumerate(self.Sequence_hub)
                    if sequence.iteration == k
                ),
                None,
            )
            #print(f"index:{index}")

            new_width = width
            new_start_time = start_time
            if function_width != "":  
                # the pulse added varies in width (duration)

                # the variables on the funct_str must be W and i
                W = width

                # here we need to make for example if iter range [50,55] and 
                # i=50 we need x=1, the +1 is for it to start in 1 and not 0
                i = k - iteration_range[0] + 1
                new_width = eval(function_width)  # varied width
                #print(f"function width:{function_width}, new_width:{new_width}")

            if function_start != "":  
                # the pulse added varies in start_time
                S = start_time
                i = k - iteration_range[0] + 1
                new_start_time = eval(function_start)  # varied start time
                #print(
                #    f"function start_time:{function_start}, new_start_time:{new_start_time}"
                #)

            new_end_time = new_start_time + new_width
            if new_end_time > max_end_time:
                # we do this to keep track of the biggest end time 
                # of the added pulse to then compare to the biggest
                # end time of every iteration, this is gonna be 
                # eventually used for display
                max_end_time = new_end_time 

            if index == None:  # no sequences created
                sequence_inst = Sequence(k, self.tag, self.binary)
                #print(f"first sequence on{k} created")
                sequence_inst.add_pulse(
                    new_start_time, new_width, self.delay[0], self.delay[1]
                )
                self.Sequence_hub.append(sequence_inst)

                # error: because when i=1 after i=0 a Sequence is created but it's on sequence_hub[0] thus sequence_hub[1] will be out of range
            elif (
                self.Sequence_hub[index].iteration == k
            ):  # this means there is already a sequence for this iteration
                #print(f"sequence edited in {k}")
                self.Sequence_hub[index].add_pulse(
                    new_start_time, new_width, self.delay[0], self.delay[1]
                )  # we add the pulse to the sequence)

        self.Sequence_hub = sorted(
            self.Sequence_hub, key=lambda sequence: sequence.iteration
        )  # Sort (order) the  self.Sequence_hub list by the `iteration` attribute
        return max_end_time, True

    def a_experiment(self, i):
        """if we find a sequence for the iteration i we return the values if not we return None.
        This method is mainly to fetch data for the experiment"""
        for seq in self.Sequence_hub:
            if seq.iteration == i:
                return [
                    seq.pb_pulses,
                    seq.max_end_time_pb,
                ]  # since its for the experiment we only need to do pb_  for this
        return None

    def a_display(self, i):
        """if we find a sequence for the iteration i we return the values if not we return None.
        This method is mainly to fetch data for the display"""
        for seq in self.Sequence_hub:
            if seq.iteration == i:
                return (
                    seq.pulses
                )  # since its for the experiment we only need to do pb_  for this
        return None


class Sequence(QObject):  


    def __init__(self, iteration, tag, binary):

        super().__init__() 
        self.tag = tag  # the channel tag (ex: PB0, PB1, etc)
        self.binary = binary

        # iteration of the sequence, meaning ex:the sequence 
        # appears in the 50th iteration of the experiment
        self.iteration = iteration  

        # list of the instances of pulses of this particular sequence 
        # that will be sent to the pulse blaster (accounting for delays)
        self.pb_pulses = []
        
        # list of the instances of pulses shown in the simulation.
        self.pulses = [] 

        # end time of the sequence, will be used to check if
        # the pulse blaster is ready to send the next sequence 
        self.max_end_time_pb = 0  
        self.max_end_time = 0

    def add_pulse(self, start_time, width, delay_on, delay_off):

        end_tail = start_time + width
        start_tail = start_time
        pulse = Pulse(start_tail, end_tail, self.binary)  # without delays

        end_tail = start_time + width - delay_off
        start_tail = start_time - delay_on
        pulse_pb = Pulse(start_tail, end_tail, self.binary)  # with delays
        
        if end_tail > self.max_end_time_pb:  
            # we upddate the max end time fo the sequence if necessary
            self.max_end_time_pb = end_tail
        
        # check if the pulse doesn't overlap
        status = self.check_pulse_fusion(pulse_pb, pulse)  
        #print(f"Fusion?: {status[2]}, new pulse:{status[0]}")

        if status[2] == True:  # if there is no overlap with the fixed pulses
            # we create a new pulse with the fused intervals
            new_pulse_pb = Pulse(status[0][0], status[0][1], self.binary)  
            new_pulse = Pulse(status[1][0], status[1][1], self.binary)
            self.pb_pulses.append(new_pulse_pb)
            self.pulses.append(new_pulse)
            #print(
            #    f"pb_pulses added: {new_pulse_pb.start_tail}, {new_pulse_pb.end_tail}"
            #)
        else:
            self.pb_pulses.append(pulse_pb)
            self.pulses.append(pulse)
            #print(f"pb_pulses added: {pulse_pb.start_tail} {pulse_pb.end_tail}")
        
        # now we need to sort the pb_pulses by the start tail
        self.pb_pulses = sorted(self.pb_pulses, key=lambda pb: pb.start_tail) 
        self.pulses = sorted(self.pulses, key=lambda pulse: pulse.start_tail)

        #for i in range(len(self.pb_pulses)):
            #print(
            #    f"pb_pulses{i}: [{self.pb_pulses[i].start_tail}, {self.pb_pulses[i].end_tail}]"
            #)

    def check_pulse_fusion(self, pulse_pb, pulse):
        """
        Here we must aim o see if the corresponding pulse overlaps with any of the the pb_pulses
        """
        # the value of the channel
        # we need to adjust the intervals to account for the delays
        # including the delays
        start_tail_pb = pulse_pb.start_tail
        end_tail_pb = pulse_pb.end_tail
        start_tail = pulse.start_tail
        end_tail = pulse.end_tail

        # variable to let the system know when there
        # is an overlap with the fixed pulses
        overlap_fixed_pulses = False  
        
        if len(self.pb_pulses) > 0:  
            # if there are other pulses on the same channel
            # we need to check for overlapping, and we also
            # check if the list on the index has a sublist

            # list to store the fused pulses, 
            # and check which one is the biggest
            global_fusion_pb = []  
            global_fusion = []

            indexes_delete = []  # indexes we will delete later

            for j in range(len(self.pb_pulses)):  

                # we iterate over the pb_pulses in the 
                # respective channel, to check for overlapping
                partially_left = False
                partially_right = False
                completely_inside = False
                completely_on_top = False

                # print(f"pb_pulses per iteration{j}: {self.pb_pulses[j].start_tail}, {self.pb_pulses[j].end_tail}")

                # if the the new pulse finishes after the start of the previous
                # pulse and starts before the start of the previous pulse
                partially_left = (
                    self.pb_pulses[j].start_tail <= end_tail_pb
                    and self.pb_pulses[j].start_tail > start_tail_pb
                    and self.pb_pulses[j].end_tail >= end_tail_pb
                ) 

                # if the new pulse finishes after the end of the previous 
                # pulse and starts before the end of the previous pulse
                partially_right = (
                    self.pb_pulses[j].end_tail >= start_tail_pb
                    and self.pb_pulses[j].start_tail < start_tail_pb
                    and self.pb_pulses[j].end_tail <= end_tail_pb
                ) 

                # if the new pulse starts after the start of the previous 
                # pulse and finishes before the end of the previous pulse
                completely_inside = (
                    self.pb_pulses[j].start_tail <= start_tail_pb
                    and self.pb_pulses[j].end_tail >= end_tail_pb
                )
                # if the new pulse starts before the start of the previous
                # pulse and finishes after the end of the previous pulse
                # i.e. the new pulse contains the previous pulse
                completely_on_top = (
                    self.pb_pulses[j].start_tail >= start_tail_pb
                    and self.pb_pulses[j].end_tail <= end_tail_pb
                )

                if partially_left == True:
                    fused_pulse_pb = [start_tail_pb, self.pb_pulses[j].end_tail]
                    fused_pulse = [start_tail, self.pulses[j].end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    #print(f"Partially Left")

                elif partially_right == True:
                    fused_pulse_pb = [self.pb_pulses[j].start_tail, end_tail_pb]
                    fused_pulse = [self.pulses[j].start_tail, end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    #print(f"Partially Right")

                elif completely_inside == True:
                    fused_pulse_pb = [
                        self.pb_pulses[j].start_tail,
                        self.pb_pulses[j].end_tail,
                    ]
                    fused_pulse = [self.pulses[j].start_tail, self.pulses[j].end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    #print(f"Completely Inside")

                elif completely_on_top == True:
                    fused_pulse_pb = [start_tail_pb, end_tail_pb]
                    fused_pulse = [start_tail, end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    #print(f"Completely Ontop")
                    # now we delete the pulses that we fused, so they dont overlap with the new pulse
                if (
                    partially_left == True
                    or partially_right
                    or completely_inside == True
                    or completely_on_top
                ):
                    indexes_delete.append(j)
                    # print(f"index to delete{j}")

            if len(global_fusion_pb) > 0:  # we fuse everything that was fused
                fused_pulse_pb = self.fuse_pulses(
                    global_fusion_pb
                )  # we find the biggest pulse t
                # print(f"GLobal_fused_pulse:{global_fusion_pb} and fuse pulses:{fused_pulse_pb}")
                fused_pulse = self.fuse_pulses(global_fusion)
                for index in sorted(indexes_delete, reverse=True):
                    """
                    we delete the pulses that were already fused from the list
                    is used in the sorted() function to sort the indices in
                    descending order (from largest to smallest). This ensures that
                      when you delete elements from the list using their indices, you start
                      with the largest index first.
                      here we run with a typical
                    """
                    # print(f"pulse to be deleted:{self.pb_pulses[index].start_tail,self.pb_pulses[index].end_tail}")
                    del self.pb_pulses[index]
                    del self.pulses[index]

                return [fused_pulse_pb, fused_pulse, overlap_fixed_pulses]

            else:
                return [
                    [start_tail_pb, end_tail_pb],
                    [start_tail, end_tail],
                    overlap_fixed_pulses,
                ]

        else:
            return [
                [start_tail_pb, end_tail_pb],
                [start_tail, end_tail],
                overlap_fixed_pulses,
            ]

    def fuse_pulses(self, pulse_list):
        """
        When 2 or more pulses overlap, we need to fuse them into one pulse,
        this is done by taking the start and end time of the pulses and 
        creating a new pulse with the start and end time of the overlapping
        pulses however there might be multiple overlapping pulses,
        so we neeed to fuse them all together
        """
        min_value = min(pulse_list, key=lambda x: x[0])[0]
        max_value = max(pulse_list, key=lambda x: x[1])[1]
        return [min_value, max_value]

    def clear(self):
        self.pulse_list = []


class Pulse:


    def __init__(
        self, start_tail, end_tail, channel_binary
    ): 

        self.start_tail = start_tail
        self.end_tail = end_tail
        # self.channel_tag=[channel_tag] #we make it a list because later when creating the experiment, we might have 2 pulses from different channels that start at the same time.
        self.channel_binary = [
            channel_binary
        ]  # might be better to recieve the value fo the channel in binary, because later the convertion will take a lot of time


class Experiment(QObject):
    """
    This class will be focused on having the data sent to the spinapi and will have the necessary methods to convert the channel tags from decimal to binary.
    """

    def __init__(self, Exp_i_pb, iteration):
        super().__init__()
        self.Exp_i_pb = Exp_i_pb
        self.pb_sequence = []
        self.iteration = iteration
        self.max_end_time_pb = 0

    def Prepare_Exp(self):
        if len(self.Exp_i_pb) != 0:
            self.Order_Exp_i_pb()
        else:  # send error message
            pass

        #print(f"len(self.pb_sequence):{len(self.pb_sequence)}")
        for pulse in self.pb_sequence:  
            # this is just to show that it0s working it should be taken away later
            #print(
            #    f"Pulse start:{pulse.start_tail}, end:{pulse.end_tail}, channel:{pulse.channel_binary}"
            #)
            pass

    def Order_Exp_i_pb(self):
        """To order the list Exp_pb.
        Exp_pb=[pb,pb,pb...] were each pb is a list of objetcs for example
        for one pb=[pulse1, pulse2,..] were each pulse has 3 atributes,
        one is the start time another other is the end time, and the last
        atribute is the channel tag, which is a list with the channels of this pulse."""

        # Step 1: Flatten all the pulse sequences into one list
        all_pulses = [
            pulse for pb_pulse_list in self.Exp_i_pb for pulse in pb_pulse_list
        ]
        events = []
        # Step 2: Create events from every pulse's start and end times, per channel
        for pulse in all_pulses:
            for ch in pulse.channel_binary:
                events.append((pulse.start_tail, 0, ch))  # 0 = Start event
                events.append((pulse.end_tail, 1, ch))  # 1 = end event
        # Step 3: Sort events chronologically; starts before ends if times equal
        events.sort()

        self.pb_sequence = []
        active_channels = set()
        last_time = 0  # Start from 0 even if first pulse starts later

        # Step 4: Sweep through time and build new Pulse objects for each interval
        for time, event_type, channel in events:
            # Fill in idle gap if needed
            sorted_channels = sorted(
                active_channels.copy()
            )  ######### to transform them into a list
            # If the time has moved forward and some channels are active, record a Pulse
            if (
                last_time < time
            ):  # Fill in idle gap if needed with an empty pulse channel 0
                if active_channels:
                    self.pb_sequence.append(Pulse(last_time, time, sorted_channels))
                else:
                    self.pb_sequence.append(Pulse(last_time, time, [0]))  # idle pulse
            # Update active channel set
            if event_type == 0:
                active_channels.add(channel)  # Pulse started
            else:
                active_channels.discard(channel)  # Pulse ended

            # Update the time marker
            last_time = time

        return