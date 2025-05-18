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

import dataclasses


class PulsedESRLogic(LogicBase):
    """This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """

    adding_flag_to_list = Signal(str)
    adding_channel_to_list = Signal(
        int, int, int, str
    ) 
    frame_data_signal = Signal(
        list, list, int, int
    )  # this signal is used to send the data to the GUI
    next_frame_signal = Signal(int)
    add_iteration_txt = Signal(str)
    added_pulse_signal = Signal()
    error_str_signal = Signal(str)

    # Declare static parameters that can/must be declared in the qudi configuration
    # _increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _pulse_blaster_hardware = Connector(
        name="pulse_blaster_hardware", interface="PulseBlasterHardware", optional=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        self.measure = False
        self.track_intensity = False

        self.time_counter = 0
        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, "c:" + os.sep, "EXP", "testdata"),
            experiment_name="timetrace",
            exp_str="TMT",
        )

        self.added_channel_tags = (
            []
        )  # This is the list of the tags of the channels that are added to the database, used to be seld.added_channels
        self.channels = []  # alist with all the createdi instances of the channels
        self.channel_labels = []  # Find a way to get rid of these extra variables
        self.Delays_channel = []  # Find a way to get rid of these extra variables
        self.Experiment_Hub = []  # list of objects were each object is a
        self.Max_end_time = 0  # It gives you the max end time of all iterations
        self.dev = "Dev1"  # el device con su number
        self.counter_pin = "ctr0"  # ctr= counter basicamente una parte de la nih que cuenta o emite cuentas. El gate le dice en que intervalo contar
        self.gate_pin = "PFI9"
        self.max_variations = 0

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def add_channel(
        self, channel_tag, channel_delay, channel_label, channel_count
    ):  # Only function is to add the channel to the database if the conditions are met, it communicates with the GUI
        """
        Adds a channel to the database.
        """
        # Logic to add a channel to the database
        channel_tag = int(channel_tag)
        flag = [channel_tag, channel_delay, channel_label]

        if (
            channel_tag not in self.added_channel_tags
        ):  # Check if channel is already added, #flag[0]
            # This is for the Graphs in the Sequence Plot
            if channel_label in [
                "green",
                "yellow",
                "red",
                "apd",
                "microwave",
                "blue",
                "pink",
                "orange",
            ]:
                flag_str = f"channel: {flag[0]}, delay_on: {abs(flag[1][0])}, delay_off: {abs(flag[1][1])}, {flag[2]}"  # Convert list to string
                self.adding_flag_to_list.emit(flag_str)  # emit the signal to the GUI
                self.adding_channel_to_list.emit(
                    channel_tag, channel_delay[0], channel_delay[1], channel_label
                )
                channel_binary = self.convert_to_binary(
                    channel_tag, channel_count
                )  # channel count is the amount of ports in the ni
                self.added_channel_tags.append(flag[0])  # add channel to the set
                channel = Channel(
                    channel_tag, channel_binary, channel_label, channel_delay
                )
                self.channels.append(channel)
                self.channels = sorted(
                    self.channels, key=lambda ch: ch.tag
                )  # we order the self.channels list by their tag value
                print(f"channel color: {channel.label}")

            else:
                # print('Emitted')
                self.error_str_signal.emit(
                    f"Label {channel_label} not recognized. Please use one of the following: green, yellow, red, apd, microwave"
                )
        else:
            self.error_str_signal.emit(f"Channel {channel_tag} already added")

        return flag

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
                    max_end_time_added_sequence = channel.a_sequence(
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
        print(f"self.Max_end_time:{self.Max_end_time}")

    @Slot(int, int)
    def run_experiment(self, value_loop: int, Type: int):
        """here we iterate through each iteration of the loop to find the channels that have a sequence for that iteration
        then we order the pulses form the channels that have pulses in this iteration. Then we create an object from the
        class experiment. which we then add to our list Experiment_Hub
        """
        list_type_cero = []
        max_end_times_vars = []  # max end times per variation
        for i in range(1, self.max_variations + 1):
            print(f"Creating exp:{i}")
            Exp_i_pb = []
            max_end = 0
            for channel in self.channels:
                print("Inside the channel loop")
                print(f'i= {i}')
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

            self.Experiment_Hub.append(exp) 
            list_type_cero.append(exp.pb_sequence)


        divide_exp = self.divide_iter_experiment(value_loop)

        if Type == 0:
            """
            Variation Type A: Loop each variation x times individually
            (v1), (v1), ..., (v1), (v2), (v2), ..., (v2), (v3), (v3), ..., (v3)
            Each variation is looped x times
            """
            self.program_pulse_type_a(
                list_type_cero, value_loop, max_end_times_vars, divide_exp
            )

        elif Type == 1:
            """
            Variation Type B: Loop all variations consecutively
            (v1, v2, v3), (v1, v2, v3), (v1, v2, v3), ... x times
            """
            self.program_pulse_type_b(
                list_type_cero, value_loop, max_end_times_vars, divide_exp
            )
        """
        Calculate the max end time of the experiment: value_loop*1*duration_of_variation[k]*1.2 + value_loop*1*duration_of_variation[k+1]*1.2 + ......
        """
        """ THIS IS  FOR THE APD """
        #for channel in self.channels:
        #    if channel.label == "apd":
        #        counts = counter.read(value_loop, timeout=timeout)
        #        count_0 = counts[0]
        #        counts = np.diff(
        #            counts
        #        )  # instead of accumulating values ex (5,11,21) it gives (5,6,10)
        #        print(counts)
        #    pass

    def program_pulse_type_a(self, Flat_exp, value_loop, max_end_times_vars, divided_value):

        """here we must iterate each variation a number of value_loop times. we do this for all variations so.
        However to the pulse blaster can only have about 40k instructions and the loop can only iterate a
         maximum of 1 million times. so to get around this  we divide the value_loop by 10k iterations of the experiment
        """
        print("sending to pulse blaster")
        print(f"len(Flat_exp):{len(Flat_exp)}")
        print(f"divided_value:{divided_value}")
        print(f"max_end_times_vars:{max_end_times_vars}")
        print(f"flat_exp:{Flat_exp}")
        print(f"value_loop:{value_loop}")
        #print(f"counter:{counter}")

        spinapi.pb_close()
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            exit(-1)
        spinapi.pb_reset()
        spinapi.pb_core_clock(500)
        spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)
        ### muc add another for, to diviude the value_loop

        for d in range(0, len(divided_value)):
            # In case the x amount of loops is greater than 10k
            # the x is divided in steps of 10k
            print(f'Starting loop x={d}')
            value_loop = divided_value[d]
            print(f'value_loop={value_loop}')
            for j in range(0, self.max_variations):
                """
                For each iteration j (a variation) , we will send one set of instructions to the pulse blaster
                """
                print(f"Starting the {j}th variation")
                self._pulse_blaster_hardware().program_looped_variation(
                    Flat_exp[j],
                    value_loop
                )
                self._pulse_blaster_hardware().start()
                #start_time = time.perf_counter()
                time_wait = time_wait = max_end_times_vars[j] * value_loop * 1000
                print(f"time_wait:{time_wait}")
                self.busy_wait_us(
                    time_wait
                )  # Intended wait: minimum wait time until the next variation
                #end_time = time.perf_counter()
                #print(
                #    f"Actual wait: {(end - start)*1e6:.2f} µs"
                #)  # to get a glimpse of the error in wait time
                # el el timepo total que espera el counter para seguir a la siguient variacion. Durante ese tiempo se toman todo los datos de una variacion. Aqui se debe calcular el maximo tiempo de cada variacion y multiplicar por value _loop
                #print(f"number_of_loops:{number_of_loops}")
                self._pulse_blaster_hardware().stop()
                #spinapi.pb_close    

    def program_pulse_type_b(self, Flat_exp, value_loop, max_end_times_vars, divided_value):

        self._pulse_blaster_hardware().start_programming()
        # Exp has structure [[pulse1, pulse2, ...], [pulse1, pulse2, ...]]
        # where [[variation1], [variation2], ...]

        for d in range(0, len(divided_value)):

            # In case the x amount of loops is greater than 10k
            # the x is divided in steps of 10k
            print(f'Starting loop x={d}')
            value_loop = divided_value[d]
            print(f'value_loop={value_loop}')
            for loop in range(0, value_loop):
                for j in range(0, self.max_variations):
                    """
                    For each iteration j (a variation) , we will send one set of instructions to the pulse blaster
                    """
                    print(f"Starting the {j}th variation")
                    self._pulse_blaster_hardware().program_looped_variation(
                        Flat_exp[j],
                        1
                    )
                    self._pulse_blaster_hardware().start()
                    start = time.perf_counter()
                    time_wait = time_wait = max_end_times_vars[j] * 1000
                    print(f"time_wait:{time_wait}")
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

    def a_Send_to_pulse_blaster(
        self, Flat_exp, value_loop, max_end_times_vars, divided_value
    ):
        """here we must iterate each variation a number of value_loop times. we do this for all variations so.
        However to the pulse blaster can only have about 40k instructions and the loop can only iterate a
         maximum of 1 million times. so to get around this  we divide the value_loop by 10k iterations of the experiment
        """
        print("sending to pulse blaster")
        print(f"len(Flat_exp):{len(Flat_exp)}")
        print(f"divided_value:{divided_value}")
        print(f"max_end_times_vars:{max_end_times_vars}")
        print(f"flat_exp:{Flat_exp}")
        print(f"value_loop:{value_loop}")
        #print(f"counter:{counter}")

        spinapi.pb_close()
        spinapi.pb_select_board(0)
        if spinapi.pb_init() != 0:
            exit(-1)
        spinapi.pb_reset()
        spinapi.pb_core_clock(500)
        spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

        ### muc add another for, to diviude the value_loop
        for d in range(0, len(divided_value)):
            # In case the x amount of loops is greater than 10k
            # the x is divided in steps of 10k
            print(f'Starting loop x={d}')
            value_loop = divided_value[d]
            print(f'value_loop={value_loop}')
            for j in range(0, self.max_variations):
                """
                For each iteration j (a variation) , we will send one set of isntrutions to the pulse blaster
                However
                """
                print(f"Starting the {j}th variation")
                spinapi.pb_start_programming(spinapi.PULSE_PROGRAM)

                # generates a loop of instruction here only one iteration
                # Exp has structure [[pulse1, pulse2, ...], [pulse1, pulse2, ...]]
                # where [[variation1], [variation2], ...]
                start = spinapi.pb_inst_pbonly(
                    int(sum(Flat_exp[j][0].channel_binary[0])),
                    spinapi.Inst.LOOP,
                    value_loop,
                    (Flat_exp[j][0].end_tail - Flat_exp[j][0].start_tail) * spinapi.us,
                )

                print(
                    f"spinapi.pb_inst_pbonly({sum(Flat_exp[j][0].channel_binary[0])},spinapi.Inst.LOOP,{value_loop},({Flat_exp[j][0].end_tail-Flat_exp[j][0].start_tail})*spinapi.us)"
                )
                for i in range(1, len(Flat_exp[j])):  
                    # we start from one because we already did the 0 index
                    print(f'i = {i}')
                    if i != len(Flat_exp[j]) - 1:
                        print(
                            f"spinapi.pb_inst_pbonly({sum(list(Flat_exp[j][i].channel_binary[0]))},spinapi.Inst.CONTINUE,0,({Flat_exp[j][i].end_tail-Flat_exp[j][i].start_tail})*spinapi.us)"
                        )
                        spinapi.pb_inst_pbonly(
                            int(sum(Flat_exp[j][i].channel_binary[0])),
                            spinapi.Inst.CONTINUE,
                            0,
                            (Flat_exp[j][i].end_tail - Flat_exp[j][i].start_tail)
                            * spinapi.us,
                        )
                    else:
                        print(
                            f"spinapi.pb_inst_pbonly({sum(list(Flat_exp[j][i].channel_binary[0]))},spinapi.Inst.CONTINUE,0,({Flat_exp[j][i].end_tail-Flat_exp[j][i].start_tail})*spinapi.us)"
                        )
                        spinapi.pb_inst_pbonly(
                            int(sum(Flat_exp[j][i].channel_binary[0])),
                            spinapi.Inst.CONTINUE,
                            0,
                            (Flat_exp[j][i].end_tail - Flat_exp[j][i].start_tail)
                            * spinapi.us,
                        )
                        print(
                            f"spinapi.pb_inst_pbonly({sum(list(Flat_exp[j][i].channel_binary[0]))},spinapi.Inst.END_LOOP,start,{Flat_exp[j][i].end_tail-Flat_exp[j][i].start_tail}"
                        )
                        spinapi.pb_inst_pbonly(
                            int(sum(Flat_exp[j][i].channel_binary[0])),
                            spinapi.Inst.END_LOOP,
                            start,
                            Flat_exp[j][i].end_tail - Flat_exp[j][i].start_tail,
                        )

                    # This instruction stops the pulse sequence.
                    # The duration is set to a very small value
                    # to ensure the stop instruction is executed
                    # almost immediately.
                    spinapi.pb_inst_pbonly(
                        int(0), spinapi.Inst.STOP, 0, 1 * spinapi.us
                    )  
                    print(
                        f"spinapi.pb_inst_pbonly(int(0),spinapi.Inst.STOP,0,0.01*spinapi.us)"
                    )
                    spinapi.pb_stop_programming()  # This function call signals the end of programming the pulse sequence. It tells the SpinAPI library that the sequence definition is complete and the pulse program can be finalized
                    print(f"spinapi.pb_stop_programming()")

                spinapi.pb_start()  # here we start the spinapi
                start = time.perf_counter()
                time_wait = max_end_times_vars[j] * value_loop
                #print(f"time_wait:{time_wait}")
                self.busy_wait_us(
                    time_wait
                )  # Intended wait: minimum wait time until the next variation
                end = time.perf_counter()
                #print(
                #    f"Actual wait: {(end - start)*1e6:.2f} µs"
                #)  # to get a glimpse of the error in wait time
                # el el timepo total que espera el counter para seguir a la siguient variacion. Durante ese tiempo se toman todo los datos de una variacion. Aqui se debe calcular el maximo tiempo de cada variacion y multiplicar por value _loop
                #print(f"value_loop:{value_loop}")
                spinapi.pb_stop()
                #spinapi.pb_close
            pass
        #counter.close()

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
        if value_loop <= 10000:
            divided_value = [value_loop]  # we only repeat the big loop once
        elif value_loop > 10000:
            difference = 0
            dv = value_loop // 10000  # this gives us the integer result of the fraction
            difference = value_loop - dv * 10000
            if difference > 0:
                length_list = dv + 1
            for h in range(0, length_list):
                if h < length_list - 1:
                    divided_value.append(10000)
                else:
                    divided_value.append(difference)
        print(f"divided_value={divided_value}")
        return divided_value

        # To recieve the counts from the apd

    def create_counter_task(self):
        """
        Todo este task es para la ni"""
        # creamos el task que lee las cuentas
        counter_task = nidaqmx.Task(
            new_task_name="T1 APD fluorescence counts"
        )  # crear el task
        # En que canal recivir las cuentas y bajo que condiciones
        counter_task.ci_channels.add_ci_count_edges_chan(
            counter=self.dev
            + "/"
            + self.counter_pin,  # pin APD en la ni, en este caso seria pin 8
            name_to_assign_to_channel="APD",
            edge=nidaqmx.constants.Edge.RISING,
            initial_count=0,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP,
        )  # ci=counter input, edges cuenta cada vez que hay una subida o bajada de una señal
        # el cuando recibir las cuentas
        counter_task.timing.cfg_samp_clk_timing(
            rate=100,
            source="/"
            + self.dev
            + "/"
            + self.gate_pin,  # cuenta segu cuando llegan las señales del gate
            active_edge=nidaqmx.constants.Edge.FALLING,  # empieza acontar cuando la señal gate baja
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=100000,
        )
        # una continuiacion de lo de arriba
        counter_task.triggers.pause_trigger.dig_lvl_src = self.gate_pin
        counter_task.triggers.pause_trigger.dig_lvl_when = (
            nidaqmx.constants.Level.LOW
        )  # que pause de contar cuando este en low
        counter_task.triggers.pause_trigger.trig_type = (
            nidaqmx.constants.TriggerType.DIGITAL_LEVEL
        )

        return counter_task

    def Stop_Experiment(self):
        """spinapi.pb_stop() #stop de program
        spinapi.pb_close() # close the pusle blaster, becasue when you want to open it again it must be close for this
        """
        pass

    def prepare_frame(self, frame_i):
        """Each time we change the value of the frame, it shows the corresponding frame in the graph
        for this we need to first identify and obtain the pulses of channes who have a sequence
        for that iterations"""
        sequences_all_channels = []
        tags_colors = []
        for channel in self.channels:
            pulses_channel = channel.a_display(
                frame_i
            )  # checks in the respective channel instance if it has a sequence for this frame, if it has a a sequence active_check will hold the pb_pulses
            if (
                pulses_channel != None
            ):  # meaning there is a sequence in this channel per the iteration i
                sequences_all_channels.append(pulses_channel)
                tags_colors.append([channel.tag, channel.label])
                pass
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
        self.channels = []
        self.channel_labels = []
        self.Delays_channel = []
        self.Experiment_Hub = []
        self.Max_end_time = 0
        self.dev = "Dev1"
        self.counter_pin = "ctr0"
        self.gate_pin = "PFI9"

    @Slot(tuple)
    def switch_pb_outputs(self, pb_status: tuple):
        """
        This function is used to switch the outputs of the pulse blaster
        """
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().stop()
        self._pulse_blaster_hardware().start_programming()
        self._pulse_blaster_hardware().program_switch_state(pb_status)
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().start()
        print(f'Switching pulse blaster outputs to {pb_status}')

    def stop_pb_outputs(self):
        """
        This function is used to stop the outputs of the pulse blaster
        """
        self._pulse_blaster_hardware().stop_programming()
        self._pulse_blaster_hardware().stop()
        print('Stopping pulse blaster outputs')



class Channel(QObject):

    def __init__(self, tag, binary, label, delay):
        super().__init__()  # Call the base class's __init__ method
        # for each channel
        self.tag = tag  # the channel tag (ex: PB0, PB1, etc)
        self.label = label
        self.delay = delay
        self.Sequence_hub = []  # in this list we keep all the sequences creates
        self.error_flag = False  # Flag to track if an error occurred
        self.binary = binary

    error_adding_pulse_channel = Signal(str)

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
            return None

        start_time_pb = start_time - self.delay[0]

        if start_time_pb < 0:
            self.error_adding_pulse_channel.emit(
                f"Pulses starts with negative time{start_time_pb}"
            )
            return None
        ############################

        """ here we need to make for example if iter 
            range [50,55] --> [1,2,3,4,5,6] to plug it into 
            the function for the new width
        """

        for k in range(
            iteration_range[0], iteration_range[1] + 1
        ):  # we iterate through the iteration range, +1 for it to include the [50,55] last bracket term
            print(f"iteration_channel_class: {k}")

            """ now we need to calculate the width of the pulse, by plugging the initial width and the current 
            iteration on the function."""

            # parameter to be replaced in the function
            """generator expression: enumerate provides both the index and the element while iteratinf throught the list. next() efficiently 
                finds the first match without iterating through the entire list"""
            index = next(
                (
                    j
                    for j, sequence in enumerate(self.Sequence_hub)
                    if sequence.iteration == k
                ),
                None,
            )
            print(f"index:{index}")

            new_width = width
            new_start_time = start_time
            if function_width != "":  # the pulse added varies in width (duration)
                # vthe variables on the funct_str must be W and i
                W = width
                i = (
                    k - iteration_range[0] + 1
                )  # here we need to make for example if iter range [50,55] and i=50 we need x=1, the +1 is for it to start in 1 and not 0
                new_width = eval(function_width)  # varied width
                print(f"function width:{function_width}, new_width:{new_width}")

                # print(f"varied_width: {new_width}")
            if function_start != "":  # the pulse added varies in start_time
                S = start_time
                i = k - iteration_range[0] + 1
                new_start_time = eval(function_start)  # varied width
                print(
                    f"function start_time:{function_start}, new_start_time:{new_start_time}"
                )

            new_end_time = new_start_time + new_width
            if new_end_time > max_end_time:
                max_end_time = new_end_time  # we do this to keep track of the biggest end time of the added pulse to then compare to the biggest end time of every iteration, this is gonna be eventually used for display

            if index == None:  # no sequences created
                sequence_inst = Sequence(k, self.tag, self.binary)
                print(f"first sequence on{k} created")
                sequence_inst.add_pulse(
                    new_start_time, new_width, self.delay[0], self.delay[1]
                )
                self.Sequence_hub.append(sequence_inst)
                # sequence_inst.error_adding_pulse.connect(self.error_adding_pulse_channel.emit)

                # error: because when i=1 after i=0 a Sequence is created but it's on sequence_hub[0] thus sequence_hub[1] will be out of range
            elif (
                self.Sequence_hub[index].iteration == k
            ):  # this means there is already a sequence for this iteration
                print(f"sequence edited in {k}")
                self.Sequence_hub[index].add_pulse(
                    new_start_time, new_width, self.delay[0], self.delay[1]
                )  # we add the pulse to the sequence)

        self.Sequence_hub = sorted(
            self.Sequence_hub, key=lambda sequence: sequence.iteration
        )  # Sort (order) the  self.Sequence_hub list by the `iteration` attribute
        return max_end_time

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


class Sequence(
    QObject
):  # A sequence per iteration ( 1 frame), QObject allows signasl to work
    def __init__(self, iteration, tag, binary):
        super().__init__()  # Call the base class's __init__ method
        self.tag = tag  # the channel tag (ex: PB0, PB1, etc)
        self.binary = binary
        self.iteration = iteration  # iteration of the sequence, meaning ex: the sequence appears in the 50th iteration of the experiment
        self.pb_pulses = (
            []
        )  # this is the list of the instances of pulses of this particular sequence that will be sent to the pulse blaster (accounting for delays)
        self.pulses = (
            []
        )  # this is the list of the instances of pulses shown in the simulation.
        # elf.Channel_Pulse_iter=[] # this is the list of the pulses in the channel, it will be used to check for overlapping, WE MIGHT NOT NEED THIS
        self.max_end_time_pb = 0  # this is the end time of the sequence, it will be used to check if the pulse blaster is ready to send the next sequence
        self.max_end_time = 0

    ######   ••••••ADDING A PULSE •••••••
    def add_pulse(self, start_time, width, delay_on, delay_off):
        end_tail = start_time + width
        start_tail = start_time
        pulse = Pulse(start_tail, end_tail, self.binary)  # without delays

        end_tail = start_time + width - delay_off
        start_tail = start_time - delay_on
        pulse_pb = Pulse(start_tail, end_tail, self.binary)  # with delays
        if (
            end_tail > self.max_end_time_pb
        ):  # we upddate the max end time fo the sequence if necessary
            self.max_end_time_pb = end_tail
        status = self.check_pulse_fusion(
            pulse_pb, pulse
        )  # check if the pulse doensnt overlap
        print(f"Fusion?: {status[2]}, new pulse:{status[0]}")
        if status[2] == True:  # if there is no overlap with the fixed pulses
            new_pulse_pb = Pulse(
                status[0][0], status[0][1], self.binary
            )  # we create a new pulse with the fused intervals
            new_pulse = Pulse(status[1][0], status[1][1], self.binary)
            self.pb_pulses.append(new_pulse_pb)
            self.pulses.append(new_pulse)
            print(
                f"pb_pulses added: {new_pulse_pb.start_tail}, {new_pulse_pb.end_tail}"
            )
        else:
            self.pb_pulses.append(pulse_pb)
            self.pulses.append(pulse)
            print(f"pb_pulses added: {pulse_pb.start_tail} {pulse_pb.end_tail}")
        # now we need to sort the pb_pulses by the start tail
        self.pb_pulses = sorted(
            self.pb_pulses, key=lambda pb: pb.start_tail
        )  # Sort (order) the  self.pb_pulses list by the `start_tail` attribute
        self.pulses = sorted(self.pulses, key=lambda pulse: pulse.start_tail)
        for i in range(len(self.pb_pulses)):
            print(
                f"pb_pulses{i}: [{self.pb_pulses[i].start_tail}, {self.pb_pulses[i].end_tail}]"
            )

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

        overlap_fixed_pulses = False  # we define this variable to let the system know when there is an overlap with the fixed pulses
        # we define this variable to let the system know when there is an overlap with the fixed pulses

        if (
            len(self.pb_pulses) > 0
        ):  # if there are other puslse on the same channel we need to check for overlapping, and we also check if the list on the index has a sublist
            global_fusion_pb = (
                []
            )  # we create a list to store the fused pulses, and then check which one is the biggest
            global_fusion = []

            indexes_delete = []  # indexes we will delete later
            for j in range(
                len(self.pb_pulses)
            ):  # we iterate over the pb_pulses in the respective channel, to check for overlapping
                Partially_Left = False
                Partially_Right = False
                Completely_Inside = False
                Completely_Ontop = False
                # print(f"pb_pulses per iteration{j}: {self.pb_pulses[j].start_tail}, {self.pb_pulses[j].end_tail}")
                Partially_Left = (
                    self.pb_pulses[j].start_tail <= end_tail_pb
                    and self.pb_pulses[j].start_tail > start_tail_pb
                    and self.pb_pulses[j].end_tail >= end_tail_pb
                )  # if the the new pulse finishes after the start of the previous pulse and starts before the start of the previous pulse
                Partially_Right = (
                    self.pb_pulses[j].end_tail >= start_tail_pb
                    and self.pb_pulses[j].start_tail < start_tail_pb
                    and self.pb_pulses[j].end_tail <= end_tail_pb
                )  # if the new pulse finishes after the end of the previous pulse and starts before the end of the previous pulse
                Completely_Inside = (
                    self.pb_pulses[j].start_tail <= start_tail_pb
                    and self.pb_pulses[j].end_tail >= end_tail_pb
                )  # if the new pulse starts after the start of the previous pulse and finishes before the end of the previous pulse
                Completely_Ontop = (
                    self.pb_pulses[j].start_tail >= start_tail_pb
                    and self.pb_pulses[j].end_tail <= end_tail_pb
                )
                """ Our objetvies it to fuse the overlapping pulses, into one pulse"""
                if Partially_Left == True:
                    "we fuse the pulses together"
                    fused_pulse_pb = [start_tail_pb, self.pb_pulses[j].end_tail]
                    fused_pulse = [start_tail, self.pulses[j].end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    print(f"Partially Left")

                elif Partially_Right == True:
                    fused_pulse_pb = [self.pb_pulses[j].start_tail, end_tail_pb]
                    fused_pulse = [self.pulses[j].start_tail, end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    print(f"Partially Right")

                elif Completely_Inside == True:
                    fused_pulse_pb = [
                        self.pb_pulses[j].start_tail,
                        self.pb_pulses[j].end_tail,
                    ]
                    fused_pulse = [self.pulses[j].start_tail, self.pulses[j].end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    print(f"Completely Inside")

                elif Completely_Ontop == True:
                    fused_pulse_pb = [start_tail_pb, end_tail_pb]
                    fused_pulse = [start_tail, end_tail]
                    global_fusion_pb.append(fused_pulse_pb)
                    global_fusion.append(fused_pulse)
                    overlap_fixed_pulses = True
                    print(f"Completely Ontop")
                    # now we delete the pulses that we fused, so they dont overlap with the new pulse
                if (
                    Partially_Left == True
                    or Partially_Right
                    or Completely_Inside == True
                    or Completely_Ontop
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
        When 2 or more pulses overlap, we need to fuse them into one pulse, this is done by taking the start and end time
          of the pulses and creating a new pulse with the start and end time of the overlapping pulses
          however there might be multiple overlapping pulses, so we neeed to fuse them all together
        """
        min_value = min(pulse_list, key=lambda x: x[0])[0]
        max_value = max(pulse_list, key=lambda x: x[1])[1]
        return [min_value, max_value]

    def clear(self):
        self.pulse_list = []

    def get_display_list(self):
        """
        Returns a list with the pulse information for display.

        # Probably need some adjustments
        """
        display_list = []
        """for pulse in self.pulse_list:
            display_list.append((pulse.pulse_delay, pulse.pulse_width, pulse.pulse_channel_tag))"""
        return display_list

    ##### •••••• EXPERIMENT
    def experiment(self):
        pass


class Pulse:

    def __init__(
        self, start_tail, end_tail, channel_binary
    ):  # we dont need the delay, right??
        self.start_tail = start_tail
        self.end_tail = end_tail
        # self.channel_tag=[channel_tag] #we make it a list because later when creating the experiment, we might have 2 pulses from different channels that start at the same time.
        self.channel_binary = [
            channel_binary
        ]  # might be better to recieve the value fo the channel in binary, because later the convertion will take a lot of time


class Experiment(QObject):
    """
    This class will be focused on having the data sent to the spinapi and will have the necessarry methods to conver the channel tags from decimal to binary.
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

        print(f"len(self.pb_sequence):{len(self.pb_sequence)}")
        for pulse in self.pb_sequence:  
            # this is just to show that it0s working it should be taken away later
            print(
                f"Pulse start:{pulse.start_tail}, end:{pulse.end_tail}, channel:{pulse.channel_binary}"
            )

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


