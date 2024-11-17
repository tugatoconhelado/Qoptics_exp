import numpy as np
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QApplication
import os
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
import datetime
from pylablib.devices import Thorlabs
import dataclasses


@dataclasses.dataclass
class RotationParameterData:

    steps: int = 10
    time_per_point: int = 1
    samp_freq: int = 1000
    start: float = 0
    range: float = 360
    device: str = 'APD A'

@dataclasses.dataclass
class RotationData:

    parameters: RotationParameterData
    angle: np.ndarray
    fluorescence: np.ndarray

class PolarizationLogic(LogicBase):

    polarizer_angle_signal = Signal(float)
    data_signal = Signal(np.ndarray, np.ndarray)
    file_changed_signal = Signal(str)


    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)
    _polarizer_motor_hardware = Connector(name='polarizer_motor_hardware', interface='PolarizerMotorHardware')
    _apd_hardware = Connector(name='apd_hardware', interface='APDHardware')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization


        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='polarization',
            exp_str='PLZ'
        )
        parameters = RotationParameterData()
        self.data = RotationData(
            parameters=parameters,
            angle=np.array([]),
            fluorescence=np.array([])
        )
        self.counter = 0

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def get_intensity(self):
        pass

    @Slot(int, int, int, float, float, str)
    def start_rotation_experiment(self, steps: int, time_per_point: int,
            samp_freq: int, start: float, range: float, input: str):
        
        time_per_point = time_per_point / 1000 # convert to seconds
        self.data.parameters.steps = steps
        self.data.parameters.time_per_point = time_per_point
        self.data.parameters.samp_freq = samp_freq
        self.data.parameters.start = start
        self.data.parameters.range = range
        self.data.parameters.device = input

        range = range / 2
        angle_step = range / steps
        angles = np.arange(start, start + range, angle_step)
        self.data.angle = angles * 2
        self.data.fluorescence = np.array([])

        self.stop_acquisition()
        
        i = 0
        self.continue_acquisition = True
        while self.continue_acquisition:
            self.move_polarizer_to_angle(angles[i])
            pl_data = self.get_fluorescence(samp_freq, time_per_point)
            average = np.mean(pl_data)
            self.data.fluorescence = np.append(self.data.fluorescence, average)

            self.data_signal.emit(self.data.angle[0: i + 1], self.data.fluorescence)
            i += 1
            if i >= steps:
                break
        #self._apd_hardware().stop_apd()

    def get_fluorescence(self, samp_freq=1000, time_per_point=1):

        clock, counter = self._apd_hardware().set_apd(
            frequency=samp_freq,
            samples=int(time_per_point * samp_freq),
            continuous=True
        )
        clock.start()
        counter.start()
        fluorescence = self._apd_hardware().get_fluorescence(
            samples=int(time_per_point * samp_freq),
            frequency=samp_freq,
            time_out=1
        )
        fluorescence = np.diff(fluorescence)
        self._apd_hardware().stop()
        return fluorescence

    @Slot()
    def stop_acquisition(self):

        self._apd_hardware().stop()
        self.continue_acquisition = False
        self._polarizer_motor_hardware().stop_motor()

    @Slot(int, int)
    def move_polarizer_by_steps(self, direction, steps):

        if direction == 1:
            new_pos = self._polarizer_motor_hardware().move_by(steps)
        elif direction == -1:
            new_pos = self._polarizer_motor_hardware().move_by(-steps)
        self.polarizer_angle_signal.emit(new_pos)

    @Slot(float)
    def move_polarizer_to_angle(self, angle: float):
        new_pos = self._polarizer_motor_hardware().move_to(angle)
        self.polarizer_angle_signal.emit(new_pos)

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
            self.data_signal.emit(self.data.angle, self.data.fluorescence)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.angle, self.data.fluorescence)
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
            self.data_signal.emit(self.data.angle, self.data.fluorescence)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')

if __name__=='__main__':

    app = QApplication([])
    logic = PolarizationLogic()
    logic.initialise_motor('55217864')
    print(logic.move_to(100))
    print(logic.move_by(200))
    app.exec_()
