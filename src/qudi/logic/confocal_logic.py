import numpy as np
from PySide2.QtCore import QTimer, Signal, Slot, QThread
from PySide2.QtWidgets import QApplication
import copy
import os
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
import dataclasses


@dataclasses.dataclass
class ConfocalImageParameterData:

    pixels : tuple = (10, 10)
    scan_size : tuple = (10, 10)
    offset : tuple = (0, 0)
    pixel_time : float = 0.1

@dataclasses.dataclass
class ConfocalImageData:

    parameters : ConfocalImageParameterData = None
    counter_image_fw : np.ndarray = np.ones((10, 10))
    counter_image_bw : np.ndarray = np.ones((10, 10))
    x : np.ndarray = np.ones(10)
    y : np.ndarray = np.ones(10)

class ConfocalLogic(LogicBase):

    data_signal = Signal(np.ndarray, np.ndarray, float)
    img_size_signal = Signal(tuple, tuple, tuple)
    status_msg_signal = Signal(str)
    file_changed_signal = Signal(str)
    progress_signal = Signal(int)

    # Declare static parameters that can/must be declared in the qudi configuration
    #_increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    #_counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _apd_hardware = Connector(
        name='apd_hardware',
        interface='APDHardware',
        optional=True
    )
    _galvo_hardware = Connector(
        name='galvo_hardware',
        interface='GalvoHardware',
        optional=True
    )
    _piezo_hardware = Connector(
        name='piezo_hardware',
        interface='PiezoHardware',
        optional=True
    )
    _laser_controller_logic = Connector(
        name='laser_controller_logic',
        interface='LaserControllerLogic',
        optional=True
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        parameter_data = ConfocalImageParameterData()
        self.data = ConfocalImageData(parameters=parameter_data)
        self.measure = False
        self._mutex = Mutex()  # Mutex for access serialization
        self.filemanager = FileManager(
            data_dir=os.path.join(os.sep, 'C:' + os.sep, 'EXP', 'testdata'),
            experiment_name='confocal',
            exp_str='IMG'
        )

    def on_activate(self) -> None:
        
        pass

    def on_deactivate(self) -> None:
        pass

    @Slot(tuple, tuple, tuple, float)
    def confocal_image(self, scan_size: tuple, offset: tuple, pixels: tuple,
        pixel_time: float) -> None:

        self.stop_acquisition()

        initial_laser_power = self._laser_controller_logic()._bh_laser_hardware().power
        self._laser_controller_logic()._bh_laser_hardware().on_off_status = True
        self._laser_controller_logic()._bh_laser_hardware().frequency = 0
        self._laser_controller_logic()._bh_laser_hardware().power = 10

        # Sets parameters in data storage
        self.data.parameters.scan_size = scan_size
        self.data.parameters.offset = offset
        self.data.parameters.pixels = pixels
        self.data.parameters.pixel_time = pixel_time

        # Reports to gui statusbar
        self.status_msg_signal.emit(f'Confocal: Starting acquisition with parameters: {self.data.parameters}')
        self.img_size_signal.emit(
            self.data.parameters.scan_size,
            self.data.parameters.offset,
            self.data.parameters.pixels
        )

        parameters_log_str = (
            f'Starting scan with parameters:\n' +
            f'Scan size: {scan_size}\n' +
            f'Offset: {offset}\n' +
            f'Pixels: {pixels}\n' +
            f'Pixel time: {pixel_time}\n' +
            f'Total scan time: {pixels[0] * pixels[1] * pixel_time}'
        )
        self.log.info(parameters_log_str)

        pixel_time = pixel_time / 1000 # From ms to seconds

        # Creates data store array
        self.data.counter_image_fw = np.zeros((pixels[1], pixels[0]))
        self.data.counter_image_bw = np.zeros((pixels[1], pixels[0]))
        self.data.x = np.linspace(
            offset[0] - scan_size[0] / 2, 
            offset[0] + scan_size[0] / 2,
            pixels[0]
        )
        self.data.y = np.linspace(
            offset[1] - scan_size[1] / 2,
            offset[1] + scan_size[1] / 2,
            pixels[1]
        )

        number_samples = 2 * pixels[0] * pixels[1]
        samp_rate = float(1 / pixel_time)

        clock, scan = self._galvo_hardware().set_scan(
            scan_size=scan_size,
            offset=offset, 
            pixels=pixels, 
            pixel_time=pixel_time
        )
        clock_apd, fluorescence_reader = self._apd_hardware().set_apd(
            frequency=samp_rate, 
            samples=number_samples, 
            clock=clock
        )

        self.measure = True
        iteration = 0
        level_fluorescence = 0

        clock.start()
        fluorescence_reader.start()
        scan.start()

        # Data acquisition
        while self.measure and iteration < pixels[1]:

            # Reads the counts from the APD
            readed_counts = fluorescence_reader.read(
                number_of_samples_per_channel=int(2 * pixels[0]),
                timeout=float(2 * pixel_time * pixels[0])
            )

            readed_counts = np.array(readed_counts) * 1 / pixel_time
            self.log.debug(f'iteration: {iteration}')

            fluorescence = np.diff(readed_counts) # Convert to cps
            
            if iteration == 0:
                level_fluorescence = fluorescence[0]

            fluorescence = np.insert(
                fluorescence, -1, readed_counts[0] - level_fluorescence
            )
            
            if iteration == 0:
                fluorescence[0] = fluorescence[1]
            
            level_fluorescence = readed_counts[-1]

            forward_fluorescence = fluorescence[0: pixels[0]]
            backward_fluorescence = np.flipud(fluorescence[pixels[0]::])

            # Sets the data in the data storage
            self.data.counter_image_fw[iteration, :] = forward_fluorescence
            self.data.counter_image_bw[iteration, :] = backward_fluorescence

            # Emits the data to the gui
            self.data_signal.emit(
                copy.copy(self.data.counter_image_fw),
                copy.copy(self.data.counter_image_bw),
                iteration
            )

            progress =  int((iteration) / (pixels[1] - 1) * 100)
            self.progress_signal.emit(progress)
            QApplication.processEvents()

            if iteration >= pixels[1] - 1:
                scan.wait_until_done(timeout=2 * pixel_time * pixels[0] * pixels[1])
                self.stop_acquisition()
            iteration += 1


        self.data_signal.emit(
            copy.copy(self.data.counter_image_fw),
            copy.copy(self.data.counter_image_bw),
            iteration
        )

        self.save_data()
        self.stop_acquisition()
        self._galvo_hardware().go_to_xy_point(self.data.parameters.offset)
        self._laser_controller_logic()._bh_laser_hardware().power = initial_laser_power

    def go_to_xy_point(self, point: tuple):
    
        with self._mutex:
            self._galvo_hardware().go_to_xy_point(point)

    def go_to_z_point(self, point: tuple):

        print('confocal go to z point')
        self._piezo_hardware().go_to_z_point(point)

    def send_data(self, data):

        self.data_signal.emit(
            self.data.counter_image_fw,
            self.data.counter_image_bw,
            0
        )
        self.img_size_signal.emit(
            self.data.parameters.scan_size,
            self.data.parameters.offset,
            self.data.parameters.pixels
        )

    @Slot()
    def stop_acquisition(self):
        self.status_msg_signal.emit('Confocal: Stopping acquisition')
        self.measure = False
        self.log.info('Stopping acquisition')

        self._galvo_hardware().stop()
        self._apd_hardware().stop()
        self._piezo_hardware().stop()

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
        if filepath != '':
            for key, value in metadata.items():
                setattr(self.data.parameters, key, value)
            for key, value in data.items():
                setattr(self.data, key, value)
            self.send_data(self.data)
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
            self.send_data(self.data)
            self.log.info(f'Loaded data from {filepath}')
            self.file_changed_signal.emit(filepath)
            return filepath
    
    def delete_file(self):

        file_to_delete = self.filemanager.current_file
        self.load_previous_data()
        self.filemanager.delete(file_to_delete)
        self.log.info(f'Deleted file {file_to_delete}')

if __name__ == '__main__':

    pass

