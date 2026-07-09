import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType

def generate_circle_ao(device_name="Dev1", ch0="ao0", ch1="ao1", 
                       radius=5.0, frequency=100.0, sample_rate=10000.0):
    """
    Generates a continuous circular voltage pattern across two Analog Output channels.
    
    Parameters:
        device_name (str): NI Device identifier.
        ch0 (str): Channel for the X-axis (Cosine wave).
        ch1 (str): Channel for the Y-axis (Sine wave).
        radius (float): Amplitude of the wave in Volts (Radius of the circle).
        frequency (float): Frequency of the rotation in Hz.
        sample_rate (float): Hardware clock sampling rate in Hz.
    """
    # 1. Calculate points per single cycle to ensure perfect seamless looping
    pts_per_cycle = int(sample_rate / frequency)
    
    # 2. Generate time vector for exactly one cycle
    t = np.linspace(0, 2 * np.pi, pts_per_cycle, endpoint=False)
    
    # 3. Create X (cos) and Y (sin) waveforms
    # Stack them into a 2D array: shape must be (number_of_channels, samples_per_channel)
    x_data = radius * np.cos(t)
    y_data = radius * np.sin(t)
    waveform_data = np.vstack((x_data, y_data))
    
    # 4. Configure NI-DAQmx Task
    channel_string = f"{device_name}/{ch0},{device_name}/{ch1}"
    
    with nidaqmx.Task() as ao_task:
        # Add both analog output voltage channels
        ao_task.ao_channels.add_ao_voltage_chan(channel_string, min_val=-10.0, max_val=10.0)
        
        # Configure the hardware clock for continuous generation
        ao_task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=pts_per_cycle
        )
        
        # Write data to the buffer. 
        # auto_start=False allows us to explicitly control when the hardware begins
        ao_task.write(waveform_data, auto_start=False)
        
        print(f"Starting circular trajectory on {channel_string}...")
        print(f"Frequency: {frequency} Hz | Radius: {radius} V")
        ao_task.start()
        
        input("\nPress [Enter] to stop the analog output generation...\n")
        
        # Stop and clean up cleanly
        ao_task.stop()
        print("Task stopped safely.")

if __name__ == "__main__":
    # Example usage: Adjust Dev1, channels, and radius to match your setup
    # Python 3.8 and NI-DAQmx compatible execution block
    try:
        generate_circle_ao(
            device_name="Dev2", 
            ch0="ao0", 
            ch1="ao1", 
            radius=2.5,       # 2.5V radius = 5V peak-to-peak circle
            frequency=50.0,   # 50 Hz rotation
            sample_rate=20000.0
        )
    except nidaqmx.DaqError as e:
        print(f"NI-DAQmx Error: {e}")