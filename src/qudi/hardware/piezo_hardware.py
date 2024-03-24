
import numpy as np
import nidaqmx
import nidaqmx.stream_writers
import copy
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base


class PiezoHardware(Base):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.z_um_per_volts = 200 / 10 # 200 um / 10 V
        self.tasks = []
        self.current_z = 100

        self.settings = {
            "Device": "Dev1",
            "Analog Output Channel": "AO2",
            "Clock Source Channel": "Ctr1",
            "Clock Output Channel": "PFI13",
            "Number Samples": 20,
            "Pixel Time (ms) on movement": 5
        }

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def start_piezo(self):

        pixel_x = 10
        pixel_y = 10
        pixel_time = 0.1

        samp_rate = float(1 / pixel_time)

        range_x = 3
        range_y = 3
        number_samples = pixel_x * pixel_y
        x_volts = np.linspace(-1, 0, pixel_x) * range_x # To have in the range
        x_volts = np.tile(x_volts,pixel_y)
        y_volts = np.linspace(-1, 0, pixel_y) * range_y  # To have in the range
        y_volts = np.repeat(y_volts, pixel_x)
        xy_volts = np.array([x_volts,y_volts])


        self.clock = self.set_clock_task(
            number_samples,
            dt_pulse= pixel_time / 2
        )
        self.ao_task = self.set_analog_output(
            number_samples=number_samples,
            samp_rate=samp_rate
        )

        self.clock.start()
        writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(task_out_stream=self.ao_task.out_stream, auto_start=True)
        for i in range(1):
            written = self.ao_task.write(xy_volts, auto_start=True)

            self.ao_task.wait_until_done(timeout=pixel_time * number_samples)

        self.stop()

    def set_z_scan(self, scan_size, offset, pixels, pixel_time):

        z_values = np.linspace(
            offset[0] - scan_size[0] / 2,
            offset[0] + scan_size[0] / 2,
            pixels[0]
        )

        z_volts = z_values / self.z_um_per_volts

        clock= self.set_clock_task(
            number_samples=pixels[0],
            dt_pulse=pixel_time / 2
        )
        z_scan = self.set_analog_output(
            number_samples=pixels[0],
            samp_rate=1 / pixel_time
        )

        z_scan.write(
            z_volts,
            auto_start=False,
            timeout=pixels[0] * pixel_time
        )
        return (clock, z_scan, z_values)

    def set_analog_output(self, number_samples: int,
        samp_rate: int) -> nidaqmx.Task:
        """
        Creates the analog output task that will perform the voltage scan.

        Parameters
        ----------
        number_samples: int
            Number of samples to output.
        samp_rate: int
            Sample rate of the task.

        Returns
        -------
        task: nidaqmx.Task
            Analog output task.
        """
        ao_task_channel = (
            self.settings["Device"] +
            '/' +
            self.settings["Analog Output Channel"]
        )
        clock_source = (
            '/' +
            self.settings["Device"] +
            '/' +
            self.settings["Clock Output Channel"]
        )
        task = nidaqmx.Task(new_task_name='Piezo Analog Output')
        task.ao_channels.add_ao_voltage_chan(
            physical_channel=ao_task_channel,
            name_to_assign_to_channel='',
            min_val=0,
            max_val=10.0,
            units=nidaqmx.constants.VoltageUnits.VOLTS
        )
        task.timing.cfg_samp_clk_timing(
            rate= samp_rate,
            source=clock_source,
            active_edge=nidaqmx.constants.Edge.RISING,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

    def set_clock_task(self, number_samples: int,
            dt_pulse: float) -> nidaqmx.Task:
        """
        Creates the clock task that will perform the voltage scan.
        
        Parameters
        ----------
        number_samples: int
            Number of samples to output.
        dt_pulse: float
            Time of the pulse in seconds.
        Returns
        -------
        task: nidaqmx.Task
            Clock task.
        """
        clock_source = (
            self.settings["Device"] +
            '/' +
            self.settings["Clock Source Channel"]
        )

        task = nidaqmx.Task(new_task_name='Piezo clock')
        task.co_channels.add_co_pulse_chan_time(
            counter=clock_source,
            units=nidaqmx.constants.TimeUnits.SECONDS,
            idle_state=nidaqmx.constants.Level.HIGH,
            initial_delay=dt_pulse,
            low_time=dt_pulse,
            high_time=dt_pulse
        )
        task.timing.cfg_implicit_timing(
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_samples
        )
        self.tasks.append(task)
        return task

    def go_to_z_point(self, point: float) -> None:
        """
        Moves the piezo to a z position.
        
        Parameters
        ----------
        point: float
            Z position in um.
        """
        z0 = self.current_z
        zf = point
        #self.status_msg.emit(f'Piezo: Moving from {z0} to {zf}')
        number_samples = self.settings["Number Samples"]
        pixel_time = self.settings["Pixel Time (ms) on movement"] / 1000
        samp_rate = float(1 / pixel_time)

        
        z_volt = np.linspace(z0, zf, num=number_samples) / self.z_um_per_volts
        self.log.debug(f'z_volts = {z_volt}')

        clock = self.set_clock_task(
            number_samples=number_samples, dt_pulse=pixel_time / 2
        )
        z_movement_task = self.set_analog_output(
            number_samples=number_samples, samp_rate=samp_rate
        )

        clock.start()
        self.log.debug('starting z movement tasks')
        written = z_movement_task.write(data=z_volt, auto_start=True, timeout=pixel_time * number_samples)
        z_movement_task.wait_until_done(timeout=pixel_time * number_samples)

        self.current_z = copy.copy(zf)
        self.stop()

    def stop(self):
        """
        Stops the Piezo generation
        
        Stops and closes all the `nidaqmx.Task` that were created
        """
        self.measure = False
        self.log.debug('Stopping Piezo')
        for task in self.tasks:
            self.log.debug(f'Closing task: {task.name}')
            task.stop()
            task.close()
        self.tasks = []



