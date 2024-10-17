import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE
import nidaqmx.constants
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai1", min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)
    task.timing.cfg_samp_clk_timing(1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=10)
    data = task.read(READ_ALL_AVAILABLE)
    print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")
   
