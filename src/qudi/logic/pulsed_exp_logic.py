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
from qudi.gui.pulsed_exp.sequence_editor.structures import Sequence
import pyqtgraph as pg
import datetime
import nidaqmx
import time
import json

import dataclasses

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

        self.max_end_time = 0  # It gives you the max end time of all iterations
        self.max_variations = 10
        
        self.added_channels = []  # list of the channels that are added to the database
        self.added_pulses = []  # list of the pulses that are added to the database
        self.continue_experiment = False


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

    @Slot(Sequence, int, int, dict)
    def run_experiment(self, sequence: Sequence, loop: int = 0, repeat: int = 1, track_options: dict = None, ):
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
        self.apd_is_gated = False
        self.continue_experiment = True
        chunck_separation = loop
        divide_exp = self.divide_loops_into_chunks(
            loops=loop, separation=chunck_separation, max_separation=1_000_000
        )

        det_pulses = sequence.detector_pulses
        self.max_variations = sequence.iterations

        self.pl_data = np.zeros((repeat, self.max_variations))
        self.pl_std = np.zeros((repeat, self.max_variations))
        self.data.pl_raw_mean = np.zeros((repeat, self.max_variations, det_pulses))
        self.data.pl_raw_std = np.zeros((repeat, self.max_variations, det_pulses))

        self.data.parameters.iterations = self.max_variations
        self.data.parameters.loop = sum(divide_exp)
        self.data.parameters.repeat_exp = repeat
        self.data.parameters.sequence = "new_sequence"
        print(f'Number of apd pulses: {det_pulses}')

        if det_pulses >= 1:
            self.apd_is_gated = True

        loop_type = 0 # For now just hardcoded
        if loop_type == 0:
            """
            Variation loop_type A: Loop each variation x times individually
            (v1), (v1), ..., (v1), (v2), (v2), ..., (v2), (v3), (v3), ..., (v3)
            Each variation is looped x times
            """
            self.run_sequence_type_a(
                sequence,
                repeat,
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
                sequence,
                repeat,
                divide_exp,
                det_pulses,
                track_options
            )

        else:
            self.error_str_signal.emit(
                f"Loop type {loop_type} not recognized. Please use 0 or 1."
            )
            return
    
    def run_sequence_type_a(self, sequence: Sequence, repeat_exp, divided_value, det_pulses, track_options=None):
        """here we must iterate each variation a number of value_loop times. we do this for all variations so.
        However to the pulse blaster can only have about 40k instructions and the loop can only iterate a
         maximum of 1 million times. so to get around this  we divide the value_loop by 10k iterations of the experiment

        Parameters
        ----------
        track_options : dict, optional
            Options for tracking intensity during the experiment, by default None.
            Format: {'track': bool, 'by_repetition': bool, 'interval': int}
        """
        # Repeat loop
        for j in range(0, repeat_exp):

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

            # Iterations (variations) loop
            
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

                    print(f"Running i={i}, d={d}, j={j}, value_loop={value_loop}")
                    sequence_iteration = sequence.evaluate_iteration(i, apply_delay=True)
                    instructions = self._pulse_blaster_hardware().compile(
                        sequence_iteration,
                        loop=value_loop
                    )
                    # self._pulse_blaster_hardware().reset()
                    self._pulse_blaster_hardware().program(instructions)
                    
                    print(f"Variation duration={sequence_iteration.duration}")
                    time_wait = sequence_iteration.duration * value_loop # in ns
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
                if det_pulses == 0:
                    print("No detector pulses added, skipping data processing")
                    if not self.continue_experiment:
                        break
                    continue
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
                # time_data = eval(self.time_function, {"S": 2500, "i": x_data})
                time_data = x_data

                self.data.pl_mean = data_avg
                self.data.pl_std = data_std
                self.data.tau = time_data
                self.data_signal.emit(x_data, data_avg, data_std)
            
                
                if not self.continue_experiment:
                    break
                
            if self.apd_is_gated:
                self._apd_hardware().stop_acquisition()
                self._apd_hardware().stop()

            experiment_end = time.perf_counter()
            print(
                f"Total time for all variations in experiment repetition {j + 1} of {repeat_exp}: {(experiment_end - experiment_start) * 1000:.2f} ms"
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

    def run_sequence_type_b(self, sequence: Sequence, repeat_exp, divided_value, det_pulses, track_options=None):

        self._pulse_blaster_hardware().start_programming()
        # Exp has structure [[pulse1, pulse2, ...], [pulse1, pulse2, ...]]
        # where [[variation1], [variation2], ...]

        for d in range(0, len(divided_value)):

            # In case the x amount of loops is greater than 10k
            # the x is divided in steps of 10k
            value_loop = divided_value[d]
            for loop in range(0, value_loop):
                for j in range(0, self.max_variations):
                    """
                    For each iteration j (a variation) , we will send one set of instructions to the pulse blaster
                    """
                    self._pulse_blaster_hardware().program_looped_variation(
                        sequence[j],
                        1
                    )
                    self._pulse_blaster_hardware().start()
                    start = time.perf_counter()
                    time_wait = time_wait = sequence[j] * 1000
                    self.busy_wait_us(
                        time_wait
                    )  # Intended wait: minimum wait time until the next variation
                    end = time.perf_counter()
                    self._pulse_blaster_hardware().stop()

    def busy_wait_us(self, us):
        # Convert microseconds to seconds and add it to the current time
        # This gives us the target end time
        end = time.perf_counter() + us / 1e6

        # Loop until the current time reaches the end time
        while time.perf_counter() < end:
            pass  # This is a "busy wait" — doing nothing but checking the time

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
        self._pulse_blaster_hardware().stop()
        self._apd_hardware().stop()
        self.continue_experiment = False

    @Slot(tuple)
    def switch_pb_outputs(self, pb_status: tuple):
        """
        This function is used to switch the outputs of the pulse blaster
        """
        print(f'Switching pulse blaster outputs to {pb_status}')
        self._pulse_blaster_hardware().stop()
        self._pulse_blaster_hardware().switch_state(pb_status)

    @Slot()
    def stop_pb_outputs(self):
        """
        This function is used to stop the outputs of the pulse blaster
        """
        self._pulse_blaster_hardware().stop()
        print('Stopping pulse blaster outputs')

    def send_data(self, data):

        x_data = np.linspace(1, data.parameters.iterations, data.parameters.iterations)
        self.data_signal.emit(x_data, data.pl_mean, data.pl_std)

    @Slot()
    def save_data(self) -> None:
        """
        Saves the data to a file.

        Parameters
        ----------
        filepath : str
            Path to the file where the data will be saved
        """
        with self._mutex:
            print("About to convert to dict")
            data_dict = dataclasses.asdict(self.data)
            data_dict.pop('parameters')
            print("popped parameters")
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


