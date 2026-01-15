import nidaqmx
import nidaqmx.constants
import numpy as np
import matplotlib.pyplot as plt

def set_finite_clock(number_samples, frequency=1e3):

    clock_source_channel = 'Dev1/ctr1'
    clock_task = nidaqmx.Task(new_task_name='APD finite clock')
    clock_task.co_channels.add_co_pulse_chan_freq(
        counter=clock_source_channel,
        units=nidaqmx.constants.FrequencyUnits.HZ,
        idle_state=nidaqmx.constants.Level.LOW,
        initial_delay=0.0,
        freq=frequency,
        duty_cycle=0.5
    )
    clock_task.timing.cfg_implicit_timing(
        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
        samps_per_chan=number_samples
    )
    clock_task.triggers.start_trigger.dig_lvl_src='PFI4'
    clock_task.triggers.start_trigger.dig_lvl_when=nidaqmx.constants.Level.HIGH
    #clock_task.triggers.pause_trigger.trig_type=nidaqmx.constants.TriggerType.DIGITAL_LEVEL
    clock_task.triggers.start_trigger.retriggerable=True
    return clock_task

def create_counter_task(freq, samples, dev="Dev1", counter_pin="ctr0", gate_pin="PFI9"):

    counter_source_channel = f"{dev}/{counter_pin}"
    print(f"Counter source channel: {counter_source_channel}")
    counter_task=nidaqmx.Task(new_task_name='Gated APD Counter') 
    counter_task.ci_channels.add_ci_count_edges_chan(
        counter=counter_source_channel,
        name_to_assign_to_channel='',
        edge= nidaqmx.constants.Edge.RISING,
        initial_count=0,
        count_direction=nidaqmx.constants.CountDirection.COUNT_UP
    )
    counter_task.timing.cfg_samp_clk_timing(
        rate=freq,
        source='/Dev1/PFI13',
        active_edge=nidaqmx.constants.Edge.FALLING,
        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
        samps_per_chan=samples
    )
    counter_task.read_all_avail_samp = True
    

    return counter_task
    
if __name__ == "__main__":
    import time

    # Example usage
    dev = "Dev1"
    counter_pin = "ctr0"
    gate_pin = "PFI9"
    samples = 1000
    sample_rate = 1000  # Hz

    time_axis = np.arange(samples) / sample_rate
    
    task = create_counter_task(freq=1000, samples=1000, dev=dev, counter_pin=counter_pin, gate_pin=gate_pin)
    clock_task = set_finite_clock(number_samples=100, frequency=sample_rate)
    # Start the clock task
    task.start()
    clock_task.start()

    # Start the task
    
    time_start = time.time()

    # Wait for a while to collect data
    #task.wait_until_done(timeout=10.0)  # Wait for 10 seconds

    # Read the number of counts
    count = task.read(number_of_samples_per_channel=1000, timeout=10)

    time_finished = time.time()

    print(f"Count: {np.diff(count) * 1000}")
    print(f"Time elapsed: {time_finished - time_start}")
    plt.plot(np.diff(count)*1000)
    #plt.plot(time_axis[0:-1], np.diff(count)*1000)
    plt.show()
    # Stop the task
    task.stop()
    clock_task.stop()
    
    # Clean up
    task.close()
    clock_task.close()