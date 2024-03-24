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


@dataclasses.dataclass
class TrackingParameterData:
    
    track_interval : int = 1
    track_intensity : int = 4

@dataclasses.dataclass
class TrackingData:

    parameters : TrackingParameterData = None
    img : ConfocalImageData = None
    tracking_log : list = None


class TrackingLogic(LogicBase):

    data_signal = Signal(ConfocalImageData)
    point_profile_fit_signal = Signal(tuple, tuple, tuple)
    z_profile_fit_signal = Signal(tuple, tuple)
    save_signal = Signal()
    max_point_signal = Signal(tuple)
    max_z_signal = Signal(tuple)
    img_size_signal = Signal(tuple, tuple, tuple)
    status_msg_signal = Signal(str)

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


    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    @Slot(tuple, tuple, tuple, float)
    def confocal_image(self, scan_size: tuple, offset: tuple, pixels: tuple,
        pixel_time: float) -> np.ndarray:

        self.stop_acquisition()
        self.data.img.parameters.scan_size = scan_size
        self.data.img.parameters.offset = offset
        self.data.img.parameters.pixels = pixels
        self.data.img.parameters.pixel_time = pixel_time
        self.status_msg_signal.emit(f'Tracking: Starting scan with parameters: {self.data.img.parameters}')

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

        clock, scan = self._galvo_hardware.set_scan(
            scan_size=scan_size,
            offset=offset, 
            pixels=pixels, 
            pixel_time=pixel_time
        )
        clock_apd, fluorescence_reader = self._apd_hardware.set_apd(
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

            readed_counts = np.array(readed_counts)
            self.log.debug(f'iteration: {iteration}')

            fluorescence = np.diff(readed_counts)
            
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

            self.data_signal.emit(
                copy.copy(self.data.img.counter_image_fw)
            )

            progress =  int((iteration) / (pixels[1] - 1) * 100)
            #self.progress_signal.emit(progress)
            QApplication.processEvents()

            if iteration >= pixels[1] - 1:
                scan.wait_until_done(timeout=2 * pixel_time * pixels[0] * pixels[1])
            iteration += 1


        self.data_signal.emit(
            copy.copy(self.data.img.counter_image_fw)
        )

        self.save_signal.emit()
        self.stop_acquisition()
        self._galvo_hardware.go_to_xy_point(self.data.img.parameters.offset)
        
        return self.data.img.counter_image_fw

    @Slot(tuple, bool, int, bool, int)
    def track_point(self, offset: tuple, track_intensity: bool = False,
            track_intensity_value: int = 4, track_interval: bool = False,
            track_interval_value: int = 1) -> None:

        while self.track_point:
            self.max_xyz(point=offset)
            time.sleep(3)

    @Slot(tuple)
    def max_xyz(self, point, parameters: tuple) -> tuple:
        """
        Finds the (x, y, z) point for which the maximum of PL is found
        """
        max_point = self.max_xy(point=point)
        max_point = self.max_z(point=point)
        return max_point

    @Slot(tuple, tuple, tuple, float)  
    def max_xy(self, scan_size: tuple, offset:tuple,
            pixels: tuple, pixel_time: float) -> tuple:
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

        Returns
        -------
        max_point : tuple
            (x, y) point for which the maximum of PL is found.
        """
        point = offset
        img = self.confocal_image(
            scan_size=scan_size,
            offset=point,
            pixels=pixels,
            pixel_time=pixel_time
        )
        self.measure = True
        print('---------------------------')
        print('Looking for max (x, y) point')

        max_point = self.find_max_point(img)
        # Send max point info to the GUI #TODO

        if math.dist(point, max_point) <= 0.1:
            # Send the information to the GUI #TODO
            # Go to the point #TODO
            print('Distance is ok')
            self.max_point_signal.emit(max_point)
            self.position[0] = max_point[0]
            self.position[1] = max_point[1]
            return max_point
        elif math.dist(point, max_point) > 0.1:
            print('Distance is not ok')
            if self.keep_scanning:
                return self.max_xy(scan_size, max_point, pixels, pixel_time)

    @Slot(tuple, tuple, tuple, float)  
    def max_z(self, scan_size: tuple, offset: tuple, pixels: tuple,
            pixel_time: float) -> tuple:
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

        Returns
        -------
        max_point : tuple
            (x, y) point for which the maximum of PL is found.
        """
        z_values, z_scan = self.z_scan(scan_size, offset, pixels, pixel_time)
        self.measure = True
        self.z_profile_fit_signal.emit((z_values, z_scan), ([], []))
        max_z = self.find_max_z_point(z_values, z_scan)
        if abs(offset[0]-max_z) < 0.1:
            self._piezo_hardware.go_to_z_point(max_z)
            self.position[2] = max_z
            self.max_z_signal.emit((max_z))
            return (max_z, )
        elif abs(offset[0]-max_z) > 0.1:
            print('You wont catch me')
            #return self.max_z(max_z)

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
        print('Creating z scan')
        self.measure = True
        pixel_time = pixel_time / 1000 # From ms to seconds
        clock, z_scan, z_values = self._piezo_hardware.set_z_scan(
            scan_size, offset, pixels, pixel_time
        )

        clock_apd, fluorescence_reader = self._apd_hardware.set_apd(
            frequency=1 / pixel_time, 
            samples=pixels[0], 
            clock=clock
        )

        print('Running Z scan')
        clock.start()
        fluorescence_reader.start()
        z_scan.start()

        readed_counts = fluorescence_reader.read(
            number_of_samples_per_channel=pixels[0],
            timeout=float(pixel_time * pixels[0])
        )

        fluorescence = np.diff(readed_counts)
        fluorescence = np.insert(fluorescence, -1, readed_counts[0])
        self.stop_acquisition()
        return (z_values, fluorescence)
    
    def find_max_z_point(self, z_values: np.ndarray, z_scan: np.ndarray) -> float:
        """
        Finds the maximum of a z scan
        
        Parameters
        ----------
        z_scan : tuple
            (z_values, fluorescence) of the z scan
        """
        max_z = z_values[np.argmax(z_scan)]
        try:
            z_fit = fit_gaussian(z_values, z_scan)
            max_z = z_fit[0][1]
            print(f'Fitted gaussian: {z_fit[0]}')
            print(f'z_values: {np.min(z_values)}, {np.max(z_values)}')

            z_fit_prof = (
                    np.linspace(np.min(z_values), np.max(z_values), 500),
                    gaussian(
                        np.linspace(np.min(z_values), np.max(z_values), 500),
                        *z_fit[0])
            )

            self.z_profile_fit_signal.emit(
                    (z_values, z_scan),
                    z_fit_prof
            )
        except Exception as e:
            print(f'Error fitting: {e}')
            return max_z
        finally:
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

    def find_max_point(self, img: np.ndarray) -> tuple:
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

        Returns
        -------
        tuple
            Point for which the maximum of the image is found
        """
        print('Looking for max point')
        max_index = np.unravel_index(np.argmax(img), img.shape)

        # It may not be obvious but when the index are retreived they give the
        # (y, x) coordinates of the point. Because the method returns the 
        # (row, column) coordinates, we need to flip the index.
        max_point = (
            self.data.img.x[max_index[1]],
            self.data.img.y[max_index[0]]
        )
        fast_prof, slow_prof = self.find_img_profile_at_point(img, max_point)

        try:
            print('Trying fit')
            #fit_gaussian retruns a tuple with the fit parameters and the
            #covariance matrix. We only need the fit parameters.

            fast_fit = fit_gaussian(self.data.img.x, fast_prof)
            slow_fit = fit_gaussian(self.data.img.y, slow_prof)
            print(f"Fast axis FWHM: {fast_fit[0][2] * 2.355}")
            print(f"Slow axis FWHM: {slow_fit[0][2] * 2.355}")
            max_point = (fast_fit[0][1], slow_fit[0][1])

            print('Trying fit')

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
            print('Trying fit')
            self.point_profile_fit_signal.emit(
                max_point,
                ((self.data.img.x, fast_prof), fast_fit_prof),
                ((self.data.img.y, slow_prof), slow_fit_prof)
            )
            print('Fitted gaussian')
        except Exception as err:
            print(f'Error fitting: {err}')
            return max_point
        finally:
            print(f'Returning max point: {max_point}')
            return max_point
    
    def go_to_xy_point(self, point: tuple):
    
        self._galvo_hardware.go_to_xy_point(point)

    @Slot()
    def stop_acquisition(self):
        
        self.keep_scanning = True
        if self.measure is False:
            self.keep_scanning = False
        self.status_msg_signal.emit('Tracking: Stopping acquisition')
        self.measure = False
        self.log.info('Stopping acquisition')

        self._apd_hardware().stop()
        self._galvo_hardware().stop()
        self._piezo_hardware().stop()
