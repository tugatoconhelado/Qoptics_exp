import nidaqmx
import nidaqmx.constants
import numpy as np
import matplotlib.pyplot as plt
import time


def create_counter_task_width(samples, freq=100e6):

    counter_source_channel = "dev1/ctr0"
    gate_source_channel = "/dev1/PFI9"

    counter_task=nidaqmx.Task(new_task_name='Gated APD Counter') 
    counter_task.ci_channels.add_ci_pulse_width_chan(
        counter=counter_source_channel,
        name_to_assign_to_channel='',
        min_val=0.000000100,  # 100 ns
        max_val=18.38860750,  # 1 us
        units=nidaqmx.constants.TimeUnits.SECONDS,
        starting_edge=nidaqmx.constants.Edge.RISING
    )
    counter_task.timing.cfg_implicit_timing(
        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
        samps_per_chan=samples
    )

    counter_task.channels.ci_ctr_timebase_src = '/dev1/PFI8'
    counter_task.channels.ci_dup_count_prevention = True
    return counter_task

def create_counter_task(samples):

    counter_source_channel = "dev1/ctr0"
    counter_gate_channel = "/dev1/PFI9"

    read_task = nidaqmx.Task(new_task_name='APD fluorescence counts')

    # Adds counter input channel (counter 0)
    read_task.ci_channels.add_ci_count_edges_chan(
        counter=counter_source_channel,
        name_to_assign_to_channel='',
        edge=nidaqmx.constants.Edge.RISING,
        initial_count=0,
        count_direction=nidaqmx.constants.CountDirection.COUNT_UP
    )

    # Configures the sampling clock
    status = read_task.timing.cfg_samp_clk_timing(
        rate=100e6,
        source=counter_gate_channel,
        active_edge=nidaqmx.constants.Edge.FALLING,
        sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
        samps_per_chan=samples
    )

    #read_task.read_all_avail_samp = True
    read_task.triggers.pause_trigger.dig_lvl_src = counter_gate_channel
    read_task.triggers.pause_trigger.dig_lvl_when = nidaqmx.constants.Level.LOW
    read_task.triggers.pause_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_LEVEL
    read_task.channels.ci_dup_count_prevention = True

    return read_task

if __name__ == "__main__":
    import time

    samples = 1000

    time_axis = np.arange(samples)
    
    task = create_counter_task(samples=3*2*samples)

    data = np.array([])
    # Start the task
    task.start()

    # Read the number of counts
    for _ in range(3):
        for i in range(2):
            time.sleep(0.1)
            start_time = time.time()
            count = task.read(number_of_samples_per_channel=int(samples), timeout=10)
            print(f"Count: {count}")
            count = np.array(count)
            end_time = time.time()
            print(f"Time taken: {end_time - start_time} seconds")
            data = np.append(data, count)
        
    
    # Stop the task
    task.stop()
    task.close()

    plt.plot(data)

    plt.show()

