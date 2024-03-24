import nidaqmx
import numpy as np
from PySide2.QtCore import QObject, Signal
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base


class GalvoHardware(Base):
    """
    Models the galvo instrument
    
    Properties
    ----------
    
    Methods
    -------
    set_scan
    
    start_scan
    
    set_analog_output

    set_scan_clock

    go_to_xy_point

    stop_acquisition
    """

    status_msg_signal = Signal(str)

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        self.fast_um_per_volts = 5 / 0.80
        self.slow_um_per_volts = 5 / 1.12
        self.tasks = []
        self.current_position = (0, 0)

        self.settings = {
            "Device": "Dev1",
            "Analog Output Channel": "AO0:1",
            "Clock Source Channel": "Ctr1",
            "Clock Output Channel": "PFI13",
            "Pixel Time (ms) on movement": 5,
            "Number of steps on movement": 20
        }

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def set_scan(self, scan_size: tuple, offset: tuple, pixels: tuple, pixel_time: int):
        """
        Sets the scan parameters

        Computes the sampling rate of the clock as 1 / `pixel_time`.

        Parameters
        ----------
        scan_size: tuple
            Contains the scan size in microns as (x, y) pair
        offset: tuple
            Contains the offset position in microns as (x, y) pair
        pixel_time: int
            Time (in seconds) to stop in each pixel
        
        Returns
        -------
        scan_tasks: tuple
            Contains the clock and scan tasks. Format (clock_task, scan_task)
        """

        # Sets parameters
        pixel_x = pixels[0]
        pixel_y = pixels[1]
        range_x = scan_size[0]
        range_y = scan_size[1]
        offset_x = offset[0]
        offset_y = offset[1]

        pixel_time = pixel_time
        samp_rate = float(1 / pixel_time)
        number_samples = 2 * pixel_x * pixel_y

        # Creates scan voltage arrays
        x_volts = np.linspace(-0.5, 0.5, pixel_x) * range_x + offset_x
        x_volts = np.append(x_volts, np.flip(x_volts))
        x_volts = np.tile(x_volts, int(pixel_y))
        y_volts = np.linspace(-0.5, 0.5, pixel_y) * range_y + offset_y
        y_volts = np.repeat(y_volts, 2 * pixel_x)

        x_volts = x_volts / self.fast_um_per_volts
        y_volts = y_volts / self.slow_um_per_volts
        xy_volts = np.array([x_volts, y_volts])

        # Goes to the offset position
        self.go_to_xy_point(
            (offset[0] - scan_size[0] / 2, offset[1] - scan_size[1] / 2)
        )

        # Creates tasks
        self.clock = self.set_scan_clock(
            number_samples, dt_pulse=pixel_time / 2
        )
        self.xy_scan_task = self.set_analog_output(
            number_samples=number_samples, samp_rate=samp_rate
        )

        self.scan_volts = xy_volts
        self.timeout = float(pixel_time * pixel_x * pixel_y)
        self.xy_scan_task.write(
            self.scan_volts,
            auto_start=False,
            timeout= 10000
        )
        scan_tasks = (self.clock, self.xy_scan_task)
        return scan_tasks

    def start_scan(self):
        """
        Starts the scan task and writes the scan_volts array
        """
        #self.clock.start()
        self.xy_scan_task.start()
        written = self.xy_scan_task.write(
            self.scan_volts,
            auto_start=True,
            timeout= 10000
        )

    def set_analog_output(self, number_samples: int, samp_rate: float):
        """
        Sets the analog output tasks that will perform the voltage scan
        
        Parameters
        ----------
        number_samples: int
            Number of samples to output.
        samp_rate: float
            Sampling rate for the signal.

        Returns
        -------
        ao_task: nidaqmx.Task
            Task for the analog output scan.
        """
        clock_output_channel = '/' + self.settings['Device'] + '/' + self.settings["Clock Output Channel"]
        ao_output_channel = self.settings['Device'] + '/' + self.settings["Analog Output Channel"]

        ao_task = nidaqmx.Task(new_task_name='Galvo Analog Output')
        ao_task.ao_channels.add_ao_voltage_chan(
            physical_channel=ao_output_channel,
            name_to_assign_to_channel='',
            min_val=-10.0,
            max_val=10.0,
            units=nidaqmx.constants.VoltageUnits.VOLTS
        )
        ao_task.timing.cfg_samp_clk_timing(
            rate= samp_rate,
            source=clock_output_channel,
            active_edge=nidaqmx.constants.Edge.FALLING,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan=number_samples
        )
        self.tasks.append(ao_task)
        self.log.debug(f'Created task: {ao_task.name}')
        return ao_task

    def set_scan_clock(self, number_samples, dt_pulse):
        """
        Creates the clock that will run the scan.

        Parameters
        ----------
        number_samples: int
            Number of samples the clock will generate.
        dt_pulse: float
            Width of the clock pulse.
        
        Returns
        -------
        clock: nidaqmx.Task
            Clock task for the scan.
        """
        clock_source_channel = self.settings["Device"] + '/' + self.settings["Clock Source Channel"]
        clock_task = nidaqmx.Task(new_task_name='Galvo Scan clock')
        clock_task.co_channels.add_co_pulse_chan_time(
            counter=clock_source_channel,
            units=nidaqmx.constants.TimeUnits.SECONDS,
            idle_state=nidaqmx.constants.Level.HIGH,
            initial_delay=dt_pulse,
            low_time=dt_pulse,
            high_time=dt_pulse
        )
        clock_task.timing.cfg_implicit_timing(
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(clock_task)
        self.log.debug(f'Created task: {clock_task.name}')

        return clock_task

    def go_to_xy_point(self, point):
        """
        Goes to a given (x, y) point

        In order to move to a point, it calculates the difference between the
        current position and the new position. The movement is made in a scan
        on both axes, with a pixel time of 0.001, and with 10 steps.
        
        Parameters
        ----------
        point: tuple
            Point to move to, givenin (x, y) format.
        
        Returns
        -------
        """
        pixel_time = self.settings["Pixel Time (ms) on movement"] / 1000 # To seconds
        samp_rate = float(1 / pixel_time)
        number_samples = self.settings["Number of steps on movement"]
        
        self.status_msg_signal.emit("Galvo: Moving from (%.2f, %.2f) to (%.2f, %.2f)" % (
            float(self.current_position[0]),
            float(self.current_position[1]),
            float(point[0]),
            float(point[1])
        ))
        xf = point[0]
        yf = point[1]

        x0 = self.current_position[0]
        y0 = self.current_position[1]

        x_volt = np.linspace(x0, xf, num=number_samples) / self.fast_um_per_volts
        y_volt = np.linspace(y0, yf, num=number_samples) / self.slow_um_per_volts

        xy_volt = np.array([x_volt, y_volt])

        self.log.debug(f'x_volt = {x_volt}')
        self.log.debug(f'y_volt = {y_volt}')

        self.clock = self.set_scan_clock(
            number_samples, dt_pulse=pixel_time / 2
        )
        self.xy_movement_task = self.set_analog_output(
            number_samples=number_samples, samp_rate=samp_rate
        )
        self.clock.start()
        
        written = self.xy_movement_task.write(xy_volt, auto_start=True, timeout=pixel_time * number_samples)
        self.xy_movement_task.wait_until_done(timeout=pixel_time * number_samples)
        self.current_position = point

        self.log.info(f"Moved to x, y point: {point}")

        self.stop()

    def stop(self):
        """
        Stops the galvo acquisition
        
        Stops and closes all the `nidaqmx.Task` that were created
        """
        self.measure = False
        self.log.debug('Stopping Galvo')
        for task in self.tasks:
            self.log.debug(f'Closing task: {task.name}')
            task.stop()
            task.close()
        self.tasks = []

