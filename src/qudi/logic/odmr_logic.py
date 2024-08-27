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


@dataclasses.dataclass
class ODMRData:

    parameters: ODMRParameterData = None
    fluorescence: np.ndarray = np.ones(10)
    frequency: np.ndarray = np.ones(10)


class ODMRLogic(LogicBase):

    odmr_data_signal = Signal(np.ndarray, np.ndarray)

    # Declare connectors to other logic modules or hardware modules to interact with
    _signal_generator_hardware = Connector(name='SG384_hardware',
                                   interface='SG384Hardware')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mutex = Mutex()

        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
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

    @Slot(float, float, float, int)
    def start_acquisition(self, frequency_center: float, power: float, frequency_range: float, number_points: int):

        self.log.info('Starting acquisition')
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

        self.log.info(f'Starting acquisition with parameters: {self.data.parameters}')
        self.data.frequency = np.zeros(number_points)
        self.data.fluorescence = np.zeros(number_points)

        self.run_exp(number_points=number_points, modulation_rate=1)

    def run_exp(self, number_points, modulation_rate):

        modulation_rate = 1
        number_points = self.data.parameters.frequency_points
        sweep_time = 1 / modulation_rate
        dt = sweep_time / number_points
        timeout = sweep_time

        self.clock_task = self.set_clock(
            pulse_width= dt,
            number_samples= number_points
        )
        self.fluorescence_task = self.set_counter_fluorescence(
            number_samples=number_points
        )
        self.modulation_function_task = self.set_signal_generator_ramp_reader(
            number_samples=number_points
        )

        self.clock_task.start()
        self.fluorescence_task.start()
        self.modulation_function_task.start()

        level_fluorescence = 0
        level_volts = 0
        iteration = 0
        self.measure = True

        self.all_fluorescence = np.array([[]])

        while self.measure:


            readed_fluorescence = self.fluorescence_task.read(
                number_of_samples_per_channel=number_points,
                timeout=10
            )
            generator_ramp = self.modulation_function_task.read(
                number_of_samples_per_channel=number_points,
                timeout=10
            )

            fluorescence = np.array(readed_fluorescence)
            generator_ramp = np.array(generator_ramp)

            if iteration == 0:
                level_fluorescence = readed_fluorescence[0]
                fluorescence = np.diff(fluorescence)
                fluorescence = np.append(np.array(readed_fluorescence[1] - level_fluorescence), fluorescence)
            fluorescence = np.diff(fluorescence)
            fluorescence = np.append(np.array(readed_fluorescence[0] - level_fluorescence), fluorescence)
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
                self.all_fluorescence = np.append(self.all_fluorescence, [fluorescence], axis=0)
            averaged_fluorescence = np.average(self.all_fluorescence, axis=0)
            self.data.fluorescence = averaged_fluorescence

            self.odmr_data_signal.emit(self.data.frequency, self.data.fluorescence)

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

    def set_clock(self, pulse_width, number_samples):

        task = nidaqmx.Task()
        task.co_channels.add_co_pulse_chan_time(
            counter='Dev1/ctr1',
            name_to_assign_to_channel='Clock task',
            units=nidaqmx.constants.TimeUnits.SECONDS,
            idle_state=nidaqmx.constants.Level.HIGH,
            initial_delay=pulse_width,
            low_time=pulse_width,
            high_time=pulse_width
        )
        task.timing.cfg_implicit_timing(
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

    def set_counter_fluorescence(self, number_samples):

        task = nidaqmx.Task()
        task.ci_channels.add_ci_count_edges_chan(
            counter='Dev1/ctr0',
            name_to_assign_to_channel='Fluorescence counter task',
            edge=nidaqmx.constants.Edge.FALLING,
            initial_count=0,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        task.timing.cfg_samp_clk_timing(
            rate=1000,
            source='/Dev1/PFI13',
            active_edge=nidaqmx.constants.Edge.FALLING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples,
        )
        self.tasks.append(task)
        return task

    def set_signal_generator_ramp_reader(self, number_samples):

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
            rate=1000,
            source='/Dev1/PFI13',
            active_edge=nidaqmx.constants.Edge.FALLING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

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
            self.data_signal.emit(self.data.time_array, self.data.counts)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.time_array, self.data.counts)
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
            self.data_signal.emit(self.data.time_array, self.data.counts)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')