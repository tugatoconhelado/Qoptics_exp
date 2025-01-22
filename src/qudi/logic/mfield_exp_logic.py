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

import dataclasses

@dataclasses.dataclass
class MFieldExpParameterData:
    scan_range: int = 100
    scan_steps: float = 100

@dataclasses.dataclass
class MFieldExpData:

    parameters: MFieldExpParameterData = None
    counts: np.ndarray = np.ones(1000)
    magnet_steps: np.ndarray = np.arange(1000)

class MFieldExpLogic(LogicBase):

    data_signal = Signal(np.ndarray, np.ndarray)
    file_changed_signal = Signal(str)

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _magnet_hardware = Connector(
        name='magnet_hardware',
        interface='MagnetHardware'
    )
    _tracking_logic = Connector(
        name='tracking_logic',
        interface='TrackingLogic'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

        parameters = MFieldExpParameterData()
        self.data = MFieldExpData(parameters=parameters)
        self.measure = False

        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'c:' + os.sep, 'EXP', 'testdata'),
            experiment_name='mfield_exp',
            exp_str='MFE'
        )

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    @Slot(int, str)
    def move_magnet_to(self, position, direction):
        if direction == 'Absolute':
            self._magnet_hardware().go_to_position(position)
        elif direction == 'Forward' or direction == 'Backward':
            self._magnet_hardware().move_by_steps(position, direction)
    
    @Slot(int, int)
    def start_mag_field_scan(self, scan_range, steps):
        
        self.measure = True
        step_size = scan_range / steps
        initial_position = self._magnet_hardware().current_position
        position = initial_position
        magnet_positions = np.array([])
        fluorescence_counts = np.array([])
        for i in range(steps):
            if self.measure is True:
                position = position + step_size
                self._magnet_hardware().go_to_position(int(position))

                counts = self._tracking_logic().get_current_counts()

                magnet_positions = np.append(magnet_positions, position)
                fluorescence_counts = np.append(fluorescence_counts, counts)

                self.data.magnet_steps = magnet_positions
                self.data.counts = fluorescence_counts

                self.data_signal.emit(self.data.magnet_steps, self.data.counts)

                if i % 5 == 0:
                    self._tracking_logic().max_xyz()
            elif self.measure is False:
                break
            QApplication.processEvents()

        self._magnet_hardware().go_to_position(initial_position)

    @Slot()
    def stop_acquisition(self):
        self.measure = False
        self._magnet_hardware().stop_motor()
        self._tracking_logic().stop_acquisition()

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
            self.data_signal.emit(self.data.magnet_steps, self.data.counts)

            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)

    def load_previous_data(self):

        data, metadata, general, filepath = self.filemanager.load_previous()
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.data_signal.emit(self.data.magnet_steps, self.data.counts)
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
            self.data_signal.emit(self.data.magnet_steps, self.data.counts)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')

if __name__ == "__main__":


    sm = StepperMotorHardware()
    #sm.move_by_steps(100, 'Backward')
    sm.go_to_position(200)