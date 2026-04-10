import numpy as np
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QApplication
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.util.mutex import Mutex
from qudi.logic.filemanager import FileManager

import os
import nidaqmx

import numpy as np
import dataclasses

@dataclasses.dataclass
class ODMRParameterData:

    frequency_center: np.ndarray = np.ones(10)
    frequency_range: np.ndarray = np.ones(10)
    microwave_power: float = 0.0
    frequency_points: int = 300
    repetitions: int = 1
    number_of_averages: int = 1

@dataclasses.dataclass
class ODMRData:

    parameters: ODMRParameterData = None
    fluorescence: np.ndarray = np.ones(10)
    frequency: np.ndarray = np.ones(10)


class ODMRLogic(LogicBase):

    odmr_data_signal = Signal(np.ndarray, np.ndarray)
    odmr_full_data_signal = Signal(np.ndarray, np.ndarray)
    file_changed_signal = Signal(str)
    number_averages_signal = Signal(int)

    # Declare connectors to other logic modules or hardware modules to interact with
    _signal_generator_hardware = Connector(name='SG384_hardware',
                                   interface='SG384Hardware', optional=True)
    _tracking_logic = Connector(
        name="tracking_logic", interface="TrackingLogic", optional=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mutex = Mutex()

        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'C:' + os.sep, 'EXP', 'data'),
            experiment_name='odmr',
            exp_str='ODMR'
        )

    def on_activate(self):

        parameters = ODMRParameterData()
        self.data = ODMRData(parameters=parameters)

        self.tasks = []
        self.measure = False

    def on_deactivate(self) -> None:
        pass

    @Slot(float, float, float, int, tuple, tuple)
    def start_acquisition(self, frequency_center: float, power: float,
            frequency_range: float, number_points: int,
            track_options: tuple = (), averaging_options: tuple = ()
        ) -> None:
        """
        Start the ODMR acquisition with the given parameters.

        Configures the signal generator for a frequency sweep and
        initializes the data arrays. Then starts the acquisition loop.

        Parameters
        ----------
        frequency_center : float
            Center frequency of the microwave sweep in GHz.
        power : float
            Microwave power in dBm.
        frequency_range : float
            Frequency range of the sweep in GHz.
        number_points : int
            Number of points in the sweep.
        track_options : tuple
            Options for tracking. Contains (enabled: bool, interval: int).
            when enabled, tracking is performed every 'interval' scans.
        averaging_options : tuple
            Options for averaging. Contains (finite: bool, repetitions: int,
            stop: bool). When finite is True, the data is averaged over 
            'repetitions' scans, if finite is False, the data is averaged 
            until stopped. If stop is True,the acquisition stops after 
            the averaging is complete. Note that if finite is False, 
            stop is ignored.
        """
        self._signal_generator_hardware().configure_frequency_sweep(
            frequency_centre=frequency_center,
            amplitude=power,
            sweep_deviation=frequency_range,
            sweep_modulation_function=1,
            modulation_rate=1
        )
        self.log.info('Signal generator configured')
        self.data.parameters.frequency_center = frequency_center
        self.data.parameters.frequency_range = frequency_range
        self.data.parameters.microwave_power = power
        self.data.parameters.frequency_points = number_points

        self.log.info(
            f'Starting acquisition with parameters: {self.data.parameters}')
        self.data.frequency = np.zeros(number_points)
        self.data.fluorescence = np.zeros(number_points)

        self.average_finite = averaging_options[0]
        self.total_repetitions = averaging_options[1]
        self.stop_after_averaging = averaging_options[2]

        self.track_enabled = track_options[0]
        self.track_interval = track_options[1]

        self.run_exp(number_points=number_points, modulation_rate=1)

    def set_tasks(self, sample_rate, number_samples):
        self.clock_task = self.set_clock(
            frequency=sample_rate,
            number_samples= number_samples
        )
        self.fluorescence_task = self.set_counter_fluorescence(
            number_samples=number_samples,
            sample_rate=sample_rate
        )
        self.modulation_function_task = self.set_signal_generator_ramp_reader(
            number_samples=number_samples,
            sample_rate=sample_rate
        )
        return (
            self.clock_task,
            self.fluorescence_task,
            self.modulation_function_task
        )
    def start_acquisition_tasks(self):
        self.clock_task.start()
        self.fluorescence_task.start()
        self.modulation_function_task.start()

    def run_exp(self, number_points, modulation_rate):

        modulation_rate = 1
        number_points = self.data.parameters.frequency_points
        sweep_time = 1 / modulation_rate
        dt = sweep_time / number_points
        sample_rate = int(1 / dt)
        timeout = sweep_time

        self.set_tasks(sample_rate=sample_rate, number_samples=number_points)
        self.start_acquisition_tasks()

        level_fluorescence = 0
        level_volts = 0
        iteration = 0
        self.measure = True
        self.track_completed = False

        if self.average_finite:
            self.all_fluorescence = np.zeros((self.total_repetitions, number_points))
        elif not self.average_finite:
            self.all_fluorescence = np.array([[]])

        while self.measure:

            if self.track_enabled and self.measure:
                if (iteration + 1) % self.track_interval == 0:
                    self.stop_acquisition()
                    
                    self._tracking_logic().handle_max_request('xyz')

                    # Resume the measurement
                    self.measure = True
                    self.set_tasks(sample_rate=sample_rate, number_samples=number_points)
                    self.start_acquisition_tasks()
                    self.log.info('Resumed acquisition after tracking')
                    self.track_completed = True

            readed_fluorescence = self.fluorescence_task.read(
                number_of_samples_per_channel=number_points,
                timeout=10
            )
            generator_ramp = self.modulation_function_task.read(
                number_of_samples_per_channel=number_points,
                timeout=10
            )

            fluorescence = np.array(readed_fluorescence)
            fluorescence = fluorescence * sample_rate  # Convert to counts per sec
            readed_fluorescence = fluorescence.copy()

            generator_ramp = np.array(generator_ramp)

            if iteration == 0 or self.track_completed:
                level_fluorescence = readed_fluorescence[0]
                fluorescence = np.diff(fluorescence)
                fluorescence = np.append(fluorescence[0], fluorescence)
                level_fluorescence = readed_fluorescence[-1]
                self.track_completed = False
            else:
                fluorescence = np.diff(fluorescence)
                fluorescence = np.append(
                    np.array(
                        readed_fluorescence[0] - level_fluorescence),
                        fluorescence
                    )
                level_fluorescence = readed_fluorescence[-1]

            fluorescence = fluorescence[generator_ramp.argsort()]
            generator_ramp = generator_ramp[generator_ramp.argsort()]

            self.data.frequency = (
                self.data.parameters.frequency_center
                + self.data.parameters.frequency_range
                * generator_ramp
            )
            if iteration == 0:
                self.all_fluorescence = np.array([fluorescence])
            else:
                self.all_fluorescence = np.append(
                    self.all_fluorescence,
                    [fluorescence],
                    axis=0
                )
                if self.average_finite:
                    if self.all_fluorescence.shape[0] > self.total_repetitions:
                        self.all_fluorescence = (
                            self.all_fluorescence[-self.total_repetitions:, :]
                        )
            self.odmr_full_data_signal.emit(
                self.data.frequency,
                self.all_fluorescence
            )
            averaged_fluorescence = np.average(self.all_fluorescence, axis=0)
            self.data.parameters.number_of_averages = self.all_fluorescence.shape[0]
            self.data.fluorescence = averaged_fluorescence

            self.odmr_data_signal.emit(self.data.frequency, self.data.fluorescence)
            self.number_averages_signal.emit(self.data.parameters.number_of_averages)

            if self.average_finite and self.stop_after_averaging:
                if iteration + 1 >= self.total_repetitions:
                    self.log.info('Completed averaging, stopping acquisition')
                    self.measure = False

            iteration += 1

            QApplication.processEvents()

        self.stop_acquisition()

    @Slot()
    def stop_acquisition(self):

        self.measure = False
        self.log.info('Stopping acquisition')
        for task in self.tasks:
            self.log.info(f'Closing task: {task.name}')
            task.stop()
            task.close()
        self.tasks = []

    def set_clock(self, frequency, number_samples):

        task = nidaqmx.Task()
        task.co_channels.add_co_pulse_chan_freq(
            counter='Dev1/ctr1',
            name_to_assign_to_channel='Clock task',
            units=nidaqmx.constants.FrequencyUnits.HZ,
            idle_state=nidaqmx.constants.Level.LOW,
            initial_delay=0.0,
            freq=frequency,
            duty_cycle=0.5
        )
        task.timing.cfg_implicit_timing(
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

    def set_counter_fluorescence(self, number_samples, sample_rate):

        task = nidaqmx.Task()
        task.ci_channels.add_ci_count_edges_chan(
            counter='Dev1/ctr0',
            name_to_assign_to_channel='Fluorescence counter task',
            edge=nidaqmx.constants.Edge.RISING,
            initial_count=0,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            source='/Dev1/PFI13',
            active_edge=nidaqmx.constants.Edge.RISING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples,
        )
        self.tasks.append(task)
        return task

    def set_signal_generator_ramp_reader(self, number_samples, sample_rate):

        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            physical_channel='Dev1/AI2',
            name_to_assign_to_channel='Signal generator ramp reader task',
            terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF,
            min_val=-10,
            max_val=10,
            units=nidaqmx.constants.VoltageUnits.VOLTS,
            custom_scale_name=''
        )
        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            source='/Dev1/PFI13',
            active_edge=nidaqmx.constants.Edge.RISING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

    def send_data(self, data):
        self.odmr_data_signal.emit(self.data.frequency, self.data.fluorescence)

    def save_data(self, filepath: str = '') -> None:
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

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        self.log.info(f'Loading previous data')
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.odmr_data_signal.emit(self.data.frequency, self.data.fluorescence)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath

    def load_next_data(self):

        data, metadata, general, filepath = self.filemanager.load_next()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.odmr_data_signal.emit(self.data.frequency, self.data.fluorescence)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')