import numpy as np
import math
from PySide2.QtCore import QTimer, Signal, Slot
from PySide2.QtWidgets import QApplication
import copy
import time
import numpy as np
import copy
import os
from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.util.datastorage import TextDataStorage, ImageFormat
from qudi.logic.filemanager import FileManager
from qudi.logic.confocal_logic import ConfocalImageData, ConfocalImageParameterData
import dataclasses
from qudi.logic.fit_extra import fit_gaussian, gaussian
import functools


def set_parameters_before(function):
    
    @functools.wraps(function)
    def set_parameters(self, *args):
        self.set_tracking_parameters(*args)
        return function(self, *args)
    return set_parameters

@dataclasses.dataclass
class MaxXYParameterData:

    scan_size: tuple = ()
    offset: tuple = ()
    pixels: tuple = ()
    pixel_time: float = 0
    fit_gaussian: bool = False

@dataclasses.dataclass
class MaxZParameterData:

    scan_size: tuple = ()
    offset: tuple = ()
    pixels: tuple = ()
    pixel_time: float = 0
    fit_gaussian: bool = False

@dataclasses.dataclass
class TrackingParameterData:
    
    max_xy_parameters: MaxXYParameterData = MaxXYParameterData()
    max_z_parameters: MaxZParameterData = MaxZParameterData()
    track_interval : int = 1
    track_intensity : int = 4
    track_by_interval : bool = False
    track_by_intensity : bool = False

@dataclasses.dataclass
class TrackingData:

    parameters : TrackingParameterData = None
    img : ConfocalImageData = None
    z_profile : tuple = None
    fast_profile : tuple = None
    slow_profile : tuple = None
    tracking_log : list = None


class TrackingLogic(LogicBase):

    img_data_signal = Signal(np.ndarray)
    point_profile_fit_signal = Signal(tuple, tuple)
    point_profile_signal = Signal(np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    tracking_points_signal = Signal(np.ndarray)
    z_profile_fit_signal = Signal(tuple)
    z_profile_signal = Signal(np.ndarray, np.ndarray)
    save_signal = Signal()
    max_point_signal = Signal(tuple)
    max_z_signal = Signal(tuple)
    img_size_signal = Signal(tuple, tuple, tuple)
    status_msg_signal = Signal(str)
    call_set_offset_signal = Signal()
    tracking_finished_signal = Signal()
    start_track_intensity_signal = Signal(int, float)
    interval_clock_signal = Signal()

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

    def __init__(self,*args, **kwargs):

        super().__init__(*args, **kwargs)

        self._mutex = Mutex()
        img_parameters = ConfocalImageParameterData()
        img_data = ConfocalImageData(parameters=img_parameters)
        tracking_parameters = TrackingParameterData()
        self.data = TrackingData(parameters=tracking_parameters, img=img_data)

        self.position = [0, 0, 0]
        self.measure = True
        self.keep_scanning = True
        self.continue_tracking = True
        self.maxing_iteration = 0
        self.fit_gaussian = (True, True, True)


    def on_activate(self) -> None:
        
        # Set up a Qt timer to send periodic signals according to tracking time
        self.__timer = QTimer(parent=self)
        self.__timer.setInterval(60 * 1000)
        self.__timer.setSingleShot(False)

        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(self.interval_clock_signal.emit)

    def on_deactivate(self) -> None:
        pass

    @Slot(tuple)
    def set_fit_gaussian(self, fit_gaussian: tuple) -> None:
        """
        Sets the fit gaussian parameters for the tracking logic
        """
        self.fit_gaussian = fit_gaussian

    def set_tracking_parameters(self, xy_parameters = None, z_parameters = None, tracking_parameters = None):

        if xy_parameters is not None:
            self.data.parameters.max_xy_parameters = MaxXYParameterData(
                *xy_parameters)
        if z_parameters is not None:
            self.data.parameters.max_z_parameters = MaxZParameterData(
                *z_parameters)
        if tracking_parameters is not None:
            self.data.parameters.track_by_intensity = tracking_parameters[0][0]
            self.data.parameters.track_intensity = tracking_parameters[0][1]
            self.data.parameters.track_by_interval = tracking_parameters[1][0]
            self.data.parameters.track_interval = tracking_parameters[1][1]

    @Slot()
    def on_start_maxing(self) -> None:
        """
        Sets the maxing iteration to 0 and the keep_scanning flag to True
        so that the maxing iteration can be stopped at any time.

        This should get called before any maxing process is started by ensuring
        the signal connected to this slot is connected before the others.
        """
        self.maxing_iteration = 0
        self.keep_scanning = True

    @Slot()
    def stop_maxing(self):
        """
        Stops the maxing iteration by setting the keep_scanning flag to False
        and the maxing_iteration to 0.
        
        This slot should be connected to the user stop event
        """
        self.keep_scanning = False
        self.continue_tracking = False
        self.maxing_iteration = 0
        self.__timer.stop()

    @Slot(tuple, tuple, tuple, float)
    def confocal_image(self, scan_size: tuple, offset: tuple, pixels: tuple,
        pixel_time: float) -> np.ndarray:

        self.stop_acquisition()
        self.data.img.parameters.scan_size = scan_size
        self.data.img.parameters.offset = offset
        self.data.img.parameters.pixels = pixels
        self.data.img.parameters.pixel_time = pixel_time
        self.status_msg_signal.emit(f'Tracking: Starting scan with parameters: {self.data.img.parameters}')
        self.log.info(f'Starting scan with parameters: {self.data.img.parameters}')

        pixel_time = pixel_time / 1000 # From ms to seconds

        self.img_size_signal.emit(scan_size, offset, pixels)

        # Creates data store array
        self.data.img.counter_image_fw = np.zeros((pixels[1], pixels[0]))
        self.data.img.counter_image_bw = np.zeros((pixels[1], pixels[0]))
        self.data.img.x = np.linspace(
            offset[0] - scan_size[0] / 2, 
            offset[0] + scan_size[0] / 2,
            pixels[0]
        )
        self.data.img.y = np.linspace(
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

        while self.measure and iteration < pixels[1]:

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

            self.data.img.counter_image_fw[iteration, :] = forward_fluorescence
            self.data.img.counter_image_bw[iteration, :] = backward_fluorescence

            self.img_data_signal.emit(
                copy.copy(self.data.img.counter_image_fw)
            )

            progress =  int((iteration) / (pixels[1] - 1) * 100)
            #self.progress_signal.emit(progress)
            QApplication.processEvents()

            if iteration >= pixels[1] - 1:
                scan.wait_until_done(timeout=2 * pixel_time * pixels[0] * pixels[1])
                self.stop_acquisition()
            iteration += 1


        self.img_data_signal.emit(
            copy.copy(self.data.img.counter_image_fw)
        )

        self.save_signal.emit()
        self.stop_acquisition()
        self._galvo_hardware().go_to_xy_point(self.data.img.parameters.offset)
        
        return self.data.img.counter_image_fw

    @Slot(tuple, tuple, tuple)
    def start_tracking(self, max_xy_params: tuple, max_z_params: tuple,
        track_params: tuple) -> None:

        print('Starting tracking')
        print(track_params)

        self.data.parameters.max_xy_parameters = MaxXYParameterData(
            *max_xy_params)
        self.data.parameters.max_z_parameters = MaxZParameterData(
            *max_z_params)

        self.data.parameters.track_by_intensity = track_params[0][0]
        self.data.parameters.track_intensity = track_params[0][1]
        self.data.parameters.track_by_interval = track_params[1][0]
        self.data.parameters.track_interval = track_params[1][1]

        self.data.tracking_log = []

        self.continue_tracking = True
        
        if self.data.parameters.track_by_interval:
            self.interval_clock_signal.emit()
            self.__timer.setInterval(
                self.data.parameters.track_interval * 1000 * 60)
            self.__timer.start()

        elif self.data.parameters.track_by_intensity:
            self.track_point()
            reference_intensity = self.get_current_counts()
            self.start_track_intensity_signal.emit(
                self.data.parameters.track_intensity, reference_intensity
            )

    def get_current_counts(self):
        frequency = 1000
        samples = int(0.1 * frequency)
        clock, reader = self._apd_hardware().set_apd(
            frequency=frequency,
            samples=samples,
            continuous=True
        )
        clock.start()
        reader.start()
        #self._apd_hardware().start_apd()
        counts = self._apd_hardware().get_fluorescence(
            samples=samples,
            frequency=frequency,
            time_out=1
        )

        counts = np.diff(counts)
        mean_counts = np.mean(counts)
        counts_std = np.std(counts)

        self._apd_hardware().stop()

        return mean_counts

    @Slot()
    def track_point(self):

        if not self.continue_tracking:
            print('Stopping tracking')
            self.__timer.stop()
            return
        elif self.continue_tracking:
            position = self.max_xyz(
                dataclasses.astuple(self.data.parameters.max_xy_parameters),
                dataclasses.astuple(self.data.parameters.max_z_parameters)
            )
            self.data.tracking_log.append(position)
            print(self.data.tracking_log)
            self.tracking_points_signal.emit(np.array(self.data.tracking_log))

            self.data.parameters.max_xy_parameters.offset = position[0:2]
            self.data.parameters.max_z_parameters.offset = position[2:3]

            print(type(position[2:3]))

            print(self.data.parameters.max_xy_parameters)
            print(self.data.parameters.max_z_parameters)

            if self.data.parameters.track_by_intensity:
                reference_intensity = self.get_current_counts()
                self.start_track_intensity_signal.emit(
                    self.data.parameters.track_intensity, reference_intensity
                )
            elif self.data.parameters.track_by_interval:
                self.tracking_finished_signal.emit()

    @Slot(tuple, tuple)
    def max_xyz(self, xy_parameters: tuple, z_parameters: tuple) -> tuple:
        """
        Finds the (x, y, z) point for which the maximum of PL is found
        """
        self.log.info('Starting max_xyz')
        max_point = self.max_xy(*xy_parameters)
        self.stop_acquisition()
        max_z = self.max_z(*z_parameters)
        max_point = self.max_xy(
            xy_parameters[0], max_point, xy_parameters[2],
            xy_parameters[3], xy_parameters[4])
        return (max_point[0], max_point[1], max_z[0])

    @Slot(tuple, tuple, tuple, float, bool)  
    def max_xy(self, scan_size: tuple, offset:tuple,
            pixels: tuple, pixel_time: float, fit_gauss: bool) -> tuple:
        """
        Finds the (x, y) point for which the maximum of PL is found

        Parameters
        ----------
        scan_size : tuple
            (x, y) size of the scan.
        offset : tuple
            (x, y) offset of the scan. It is also the point to be maximised.
        pixels : tuple
            (x, y) number of pixels of the scan.
        pixel_time : float
            Time that the laser will be on each pixel.
        fit_gauss : bool
            Flag to fit a gaussian to the profile of the image.

        Returns
        -------
        max_point : tuple
            (x, y) point for which the maximum of PL is found.
        """
        self.log.info('Starting max_xy')
        self.log.info(f'Iteration: {self.maxing_iteration}')
        point = offset
        img = self.confocal_image(
            scan_size=scan_size,
            offset=point,
            pixels=pixels,
            pixel_time=pixel_time
        )
        self.stop_acquisition()
        self.measure = True
        self.log.debug('---------------------------')
        self.log.debug('Looking for max (x, y) point')

        max_point = self.find_max_point(img, fit_gauss)
        # Send max point info to the GUI #TODO

        self.maxing_iteration += 1

        if math.dist(point, max_point) <= 0.1:
            self.log.debug('Distance is ok')
            self.max_point_signal.emit(max_point)
            self.go_to_xy_point(max_point)
            self.call_set_offset_signal.emit()
            self.position[0] = max_point[0]
            self.position[1] = max_point[1]
            return max_point
        elif math.dist(point, max_point) > 0.1:
            self.log.debug('Distance is not ok')
            if self.keep_scanning:
                return self.max_xy(scan_size, max_point, pixels, pixel_time, fit_gauss)

    @Slot(tuple, tuple, tuple, float)  
    def max_z(self, scan_size: tuple, offset: tuple, pixels: tuple,
            pixel_time: float, fit_gauss: bool) -> tuple:
        """
        Finds the z position for which the maximum of PL is found

        Parameters
        ----------
        scan_size : tuple
            (x, y) size of the z scan.
        offset : tuple
            (x, y) offset of the z scan. It is also the point to be maximised.
        pixels : tuple
            (x, y) number of pixels of the z scan.
        pixel_time : float
            Time that the laser will be on each pixel.
        fit_gauss : bool
            Flag to fit a gaussian to the profile of the scan.

        Returns
        -------
        max_point : tuple
            (x, y) point for which the maximum of PL is found.
        """
        self.log.info('Starting max_z')
        self.log.info(f'Iteration: {self.maxing_iteration}')
        self.maxing_iteration += 1
        z_values, z_scan = self.z_scan(scan_size, offset, pixels, pixel_time)
        max_z = self.find_max_z_point(z_values, z_scan, fit_gauss)
        if abs(offset[0]-max_z) < 0.1:
            self.position[2] = max_z
            self.go_to_z_point(max_z)
            self.max_z_signal.emit((max_z, ))
            self.call_set_offset_signal.emit()
            return (max_z, )
        elif abs(offset[0]-max_z) > 0.1:
            if self.keep_scanning:
                return self.max_z(scan_size, (max_z, ), pixels, pixel_time, fit_gauss)

    @Slot(float)
    def go_to_z_point(self, new_point: float):
        with self._mutex:
            self._piezo_hardware().go_to_z_point(new_point)

    @Slot(tuple)
    def go_to_xy_point(self, new_point: tuple):
        with self._mutex:
            self._galvo_hardware().go_to_xy_point(new_point)

    def z_scan(self, scan_size: tuple, offset: tuple, pixels: tuple,
            pixel_time: tuple) -> tuple:
        """
        Performs a z scan with the piezo 
        
        Parameters
        ----------
        scan_size : tuple
            (z_range) size of the z scan.
        offset : tuple
            (z) offset of the z scan. It is also the point to be maximised.
        pixels : tuple
            (z_samples) number of pixels of the z scan.
        pixel_time : float
            Time that the laser will be on each pixel.

        Returns
        -------
        z_scan : np.ndarray
            Array with the counts of the z scan.
        """
        with self._mutex:
            self.stop_acquisition()
        with self._mutex:
            self.log.debug('Creating z scan')
            self.measure = True
            pixel_time = pixel_time / 1000 # From ms to seconds
            clock, z_scan, z_values = self._piezo_hardware().set_z_scan(
                scan_size, offset, pixels, pixel_time
            )
            clock_apd, fluorescence_reader = self._apd_hardware().set_apd(
                frequency=1 / pixel_time, 
                samples=pixels[0], 
                clock=clock
            )

            self.log.info('Starting Z scan')
            clock.start()
            z_scan.start()
            fluorescence_reader.start()

            readed_counts = fluorescence_reader.read(
                number_of_samples_per_channel=pixels[0],
                timeout=float(pixel_time * pixels[0])
            )
            readed_counts = np.array(readed_counts) * 1 / pixel_time
            fluorescence = np.diff(readed_counts)
            fluorescence = np.insert(fluorescence, -1, readed_counts[0])
            self.stop_acquisition()
            return (z_values, fluorescence)
    
    def find_max_z_point(self, z_values: np.ndarray, z_scan: np.ndarray, fit_gauss: bool) -> float:
        """
        Finds the maximum of a z scan
        
        Parameters
        ----------
        z_values : np.ndarray
            Z values of the z scan.
        z_scan : np.ndarray
            fluorescence of the z scan
        fit_gauss : bool
            Flag to fit a gaussian to the profile of the z scan
        """
        max_z = z_values[np.argmax(z_scan)]
        self.z_profile_signal.emit(z_values, z_scan)
        z_report_str = f'Max z: {max_z}\n'
        if not fit_gauss:
            self.log.info(f'Max point: {max_z}')
            return max_z
        try:
            z_fit = fit_gaussian(z_values, z_scan)
            max_z = z_fit[0][1]
            z_report_str += f"Fast axis FWHM: {z_fit[0][2] * 2.355}\n"
            z_report_str += f'Fitted Max point: {max_z}'
            self.log.info(z_report_str)

            z_fit_prof = (
                    np.linspace(np.min(z_values), np.max(z_values), 500),
                    gaussian(
                        np.linspace(np.min(z_values), np.max(z_values), 500),
                        *z_fit[0])
            )

            self.z_profile_fit_signal.emit(z_fit_prof)
        except Exception as e:
            self.log.info(f'Error fitting: {e}')
            return max_z
        finally:
            self.log.info(f'Max point: {max_z}')
            return max_z

    def find_img_profile_at_point(self, img: np.ndarray, point: tuple) -> tuple:
        """
        Finds the profile of the center point of an image
        """
        pixels = img.shape

        # Find the closest point in the data to the given point
        fast_axis_index = np.argmin(np.abs(self.data.img.x - point[0]))
        slow_axis_index = np.argmin(np.abs(self.data.img.y - point[1]))

        fast_axis_profile = img[slow_axis_index, :]
        slow_axis_profile = img[:, fast_axis_index]

        return (fast_axis_profile, slow_axis_profile)

    def find_max_point(self, img: np.ndarray, fit_gauss: bool) -> tuple:
        """
        Finds the maximum point of an image.

        For this, it will firstly find the profile of the image around the
        point for maximum PL. Then, it will try to fit a gaussian to the
        profile. Finally, if the fit is succesful, it will return the point
        for which the gaussian has the maximum value. Otherwise, it will just
        return the point for which the profile has the maximum value.

        Parameters
        ----------
        img : np.ndarray
            Image for which the maximum point will be found
        fit_gauss : bool
            Flag to fit a gaussian to the profile of the image

        Returns
        -------
        tuple
            Point for which the maximum of the image is found
        """
        self.log.debug('Looking for max point in find_max_point')
        max_index = np.unravel_index(np.argmax(img), img.shape)

        # It may not be obvious but when the index are retreived they give the
        # (y, x) coordinates of the point. Because the method returns the 
        # (row, column) coordinates, we need to flip the index.
        max_point = (
            self.data.img.x[max_index[1]],
            self.data.img.y[max_index[0]]
        )
        fast_prof, slow_prof = self.find_img_profile_at_point(img, max_point)
        self.point_profile_signal.emit(
            self.data.img.x, fast_prof, self.data.img.y, slow_prof)
        
        if not fit_gauss:
            self.log.info(f'Max point: {max_point}')
            return max_point

        fit_report_str = f'Max point: {max_point}\n'
        try:
            #fit_gaussian retruns a tuple with the fit parameters and the
            #covariance matrix. We only need the fit parameters.

            fast_fit = fit_gaussian(self.data.img.x, fast_prof)
            slow_fit = fit_gaussian(self.data.img.y, slow_prof)

            max_point = (fast_fit[0][1], slow_fit[0][1])
            fit_report_str += f"Fast axis FWHM: {fast_fit[0][2] * 2.355}\n"
            fit_report_str += f"Slow axis FWHM: {slow_fit[0][2] * 2.355}\n"
            fit_report_str += f'Fitted Max point: {max_point}'
            self.log.info(fit_report_str)

            fast_fit_prof = (
                np.linspace(np.min(self.data.img.x), np.max(self.data.img.x), 500),
                gaussian(
                    np.linspace(np.min(self.data.img.x), np.max(self.data.img.x), 500),
                    *fast_fit[0])
            )
            slow_fit_prof = (
                np.linspace(np.min(self.data.img.y), np.max(self.data.img.y), 500),
                gaussian(
                    np.linspace(np.min(self.data.img.y), np.max(self.data.img.y), 500),
                    *slow_fit[0])
            )
            self.point_profile_fit_signal.emit(fast_fit_prof, slow_fit_prof)

        except Exception as err:
            self.log.info(f'Error fitting: {err}')
            return max_point
        finally:
            self.log.info(f'Max point: {max_point}')
            return max_point

    @Slot()
    def stop_acquisition(self):
        """
        Stops the acquisition of the APD, the galvo and the piezo.
        
        This method should be called to stop the acquisition of an image.
        To stop the iteration process of the maxing, the stop_maxing method
        should be called.
        That way, the image acquisition can make sure that the galvo, apd and piezo
        are stopped before and after image acquisition to avoid problems.
        In other words, this method is both internal and external (user) use,
        meanwhile the stop_maxing method is only for external use.
        """
        self.measure = False
        self.log.info('Stopping acquisition')
        self.status_msg_signal.emit('Tracking: Stopping acquisition')

        self._galvo_hardware().stop()
        self._apd_hardware().stop()
        self._piezo_hardware().stop()