from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
import nidaqmx
import numpy as np



class APDHardware(Base):
    """
    Represents the APD instrument

    Attributes
    ----------
    dev
    counter_pin
    clock_pin
    clock_pfi
    clock : nidaqmx.Task
    counter : nidaqmx.Task
    count_signal : PySide2.QtCore.Signal
        Signal that contains the measured counts

    Methods
    -------
    start_apd(frequency : int, samples : int, duty_cycle : float = 0.5)
        Starts the clock and counter tasks.
    stop_apd
        Stops and closes all opened tasks.
    set_digical_pulse_train_counter(frequency : int, duty_cycle : float, samples : int)
        Creates the clock task.
    set_input_counter(frequency : int, samples : int)
        Creates the counter reader task.
    get_fluorescence(acquisition_time: float, frequency: int, time_out: float)
        Measures the average counts for a given `acquisition_time`
    """

    count_signal = Signal(float)

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the `APD` class.

        Parameters
        ----------
        dev : str
            Name of the device in which to create the tasks. Eg: 'Dev1'
        counter_pin : str
            Name of the counter in which to create the fluorescence reader task
        clock_pin : str
            Name of the counter in which to create the clock task.
        clock_pfi : str
            Name of the pin that the fluorescence reader will use as clock.

        Notes
        -----
        `clock_pfi` is supposed to be the pin that the fluorescence counter
        will use as clock. It should be the output of the `clock_pin`.
        You can check this out in NI MAX under
        devices -> right click -> device pinouts.
        """

        super().__init__(*args, **kwargs)
        
        self.tasks = []

        self.settings = {
            "Device": "Dev1",
            "Counter Source Channel": "ctr0",
            "Clock Output Channel": "PFI13",
            "Clock Source Channel": "Ctr1"
        }

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def set_apd(self, frequency : int, samples : int, duty_cycle : float = 0.5, clock: nidaqmx.Task = None, continuous: bool = False) -> bool:
        """
        Creates and sets the tasks necessary for the acquisition.

        These are the clock task and the counter task.

        Parameters
        ----------
        frequency
        samples
        duty_cycle

        Returns #ToBeImplemented
        -------
        bool
            Indicates if the operations were succesfull.
        """

        self.log.debug(f'Starting APD')
        if clock is None:
            self.clock = self.set_digital_pulse_train_clock(
                frequency=frequency, duty_cycle=duty_cycle, samples=samples
            )
        else:
            self.clock = clock
        if continuous is True:
            self.counter = self.set_continuous_counter_input(
                frequency=frequency, samples=samples
            )
        elif continuous is False:
            self.counter = self.set_input_counter(
                frequency=frequency, samples=samples
            )
        return (self.clock, self.counter)

    def start_apd(self):
        """
        Starts the clock and counter tasks
        """
        self.clock.start()
        self.counter.start()
        return True
    
    def set_finite_clock(self, number_samples, dt_pulse):
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
        clock_task = nidaqmx.Task(new_task_name='APD finite clock')
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
        
    def stop(self) -> bool:
        """
        Stops and closes all tasks in `self.tasks`

        Returns #ToBeImplemented
        -------
        bool
            Indicates if the operation were succesfull.
        """
        self.log.debug('Stopping APD')
        for task in self.tasks:
            self.log.debug(f'Closing task: {task.name}')
            task.stop()
            task.close()
        self.tasks = []
        return True

    def set_clock(self, clock: nidaqmx.Task):
        """
        Sets a nidaqmx.Task as a clock
        
        Parameters
        ----------
        clock: nidaqmx.Task
            Task to be set as clock
        """
        self.clock = clock

    def set_digital_pulse_train_clock(self, frequency : int, duty_cycle : float, samples : int) -> nidaqmx.Task:
        """
        Sets the NI card counter output that will be used as a clock signal.

        Parameters
        ----------
        frequency : int
        duty_cycle : float
        samples : int

        Returns
        -------
        nidaqmx.Task
        """
        self.log.debug('Creating digital pulse train counter task')
        clock_source_channel = self.settings["Device"] + '/' + self.settings["Clock Source Channel"]
        task = nidaqmx.task.Task(new_task_name='APD clock')
        status = task.co_channels.add_co_pulse_chan_freq(
            counter='Dev1/Ctr2',
            name_to_assign_to_channel='',
            units=nidaqmx.constants.FrequencyUnits.HZ,
            idle_state=nidaqmx.constants.Level.LOW,
            initial_delay=0.0,
            freq=frequency,
            duty_cycle=duty_cycle
        )
        status = task.timing.cfg_implicit_timing(
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=samples
        )
        self.log.debug(f'NI: Set Pulse : {status}')
        self.tasks.append(task)
        return task

    def set_input_counter(self, frequency : int, samples : int) -> nidaqmx.Task:
        """
        Set the counter in the NI card that will read the fluorescence counts.

        Parameters
        ----------
        frequency : int
            Sampling frequency.
        samples : int
            Number of samples the clock will save in buffer.

        Returns
        -------
        nidaqmx.Task
            Created task.
        """
        counter_source_channel = self.settings["Device"] + '/' + self.settings["Counter Source Channel"]
        clock_output_channel = '/' + self.settings["Device"] + '/' + self.settings["Clock Output Channel"]
        self.log.debug('Creating counter fluorescence task')
        read_task = nidaqmx.Task(new_task_name='APD fluorescence counts')
        # Adds counter input channel (counter 0)
        read_task.ci_channels.add_ci_count_edges_chan(
            counter=counter_source_channel,
            name_to_assign_to_channel='',
            edge=nidaqmx.constants.Edge.FALLING,
            initial_count=0,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        # Configures the sampling clock
        status = read_task.timing.cfg_samp_clk_timing(
            rate=frequency,
            source=clock_output_channel,
            active_edge=nidaqmx.constants.Edge.FALLING,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan=samples
        )
        self.log.debug(f'NI: Configure the clock : {status}')
        read_task.read_all_avail_samp = True
        self.tasks.append(read_task)
        return read_task

    def set_continuous_counter_input(self, frequency : int, samples : int) -> nidaqmx.Task:
        """
        Set the counter in the NI card that will read the fluorescence counts.

        Parameters
        ----------
        frequency : int
            Sampling frequency.
        samples : int
            Number of samples the clock will save in buffer.

        Returns
        -------
        nidaqmx.Task
            Created task.
        """
        counter_source_channel = self.settings["Device"] + '/' + self.settings["Counter Source Channel"]
        clock_output_channel = '/' + self.settings["Device"] + '/' + self.settings["Clock Output Channel"]
        self.log.debug('Creating counter fluorescence task')
        read_task = nidaqmx.Task(new_task_name='APD fluorescence counts')
        # Adds counter input channel (counter 0)
        read_task.ci_channels.add_ci_count_edges_chan(
            counter='Dev1/Ctr0',
            name_to_assign_to_channel='',
            edge=nidaqmx.constants.Edge.RISING,
            initial_count=0,
            count_direction=nidaqmx.constants.CountDirection.COUNT_UP
        )
        # Configures the sampling clock
        status = read_task.timing.cfg_samp_clk_timing(
            rate=frequency,
            source='/Dev1/PFI14',
            active_edge=nidaqmx.constants.Edge.RISING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=samples
        )
        self.log.debug(f'NI: Configure the clock : {status}')
        self.tasks.append(read_task)
        return read_task

    def get_fluorescence_by_time(self, acquisition_time: float, frequency: int, time_out: float) -> float:
        """
        It acquires the last `acquisition_time` data

        In order to do so it computes the number of samples to be read from
        the NI card as `acquisition_time` times `frequency`

        Parameters
        ----------
        acquisition_time : float
            Exposure time of the data to be acquired
        frequency : int
            Sampling frequency to make the acquisition. Must be the same used
            in the `start_apd()` method
        time_out : float
            Time that NI card wil wait to read data before raising and error

        Returns
        -------
        mean_counts : float
            The mean of the measured counts for the given acquisition_time
        """
        # So whats happening here is that we set the sampling clock to take 
        # frequency samples per second and we telling the task to read
        # refresh_time * frequency samples, i.e. the time that the card will
        #  acquire those data is the acquisition_time

        samples = acquisition_time * frequency
        counts = self.counter.read(
            number_of_samples_per_channel=int(samples),
            timeout=time_out
        )
        counts = np.array(counts)
        counts = np.diff(counts) # Compute diff 'cause APD measures incremental

        # Each datum in the array corresponds to 
        # refresh_time / (frequency * refresh_time) seconds so we must multiply
        # by frequency to have each datum correspond to 1 second (counts per s)
        mean_counts = np.mean(counts) * frequency

        self.log.debug(f'Returning {mean_counts}')
        self.count_signal.emit(mean_counts)
        return mean_counts

    def get_fluorescence(self, samples: int, frequency: int, time_out: float) -> float:
        """
        It acquires the last `samples` data

        After acquiring the data it transforms the measured counts to cps, by
        multiplying by the sampling frequency

        Parameters
        ----------
        samples : int
            Number of samples to read
        frequency : int
            Sampling frequency to make the acquisition. Must be the same used
            in the `start_apd()` method
        time_out : float
            Time that NI card wil wait to read data before raising and error

        Returns
        -------
        counts : np.ndarray
            Array of measured counts, converted to counts per second
        """
        # So whats happening here is that we set the sampling clock to take 
        # frequency samples per second and we telling the task to read
        # refresh_time * frequency samples, i.e. the time that the card will
        #  acquire those data is the acquisition_time

        counts = self.counter.read(
            number_of_samples_per_channel=int(samples),
            timeout=time_out
        )
        counts = np.array(counts)
        #counts = np.diff(counts) # Compute diff 'cause APD measures incremental
        # Each datum in the array corresponds to 
        # refresh_time / (frequency * refresh_time) seconds so we must multiply
        # by frequency to have each datum correspond to 1 second (counts per s)
        counts = counts * frequency

        return counts