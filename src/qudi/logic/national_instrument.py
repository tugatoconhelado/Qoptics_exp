import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE
import nidaqmx.constants
class myni:
    def __init__(self,valor):
        self.channel=valor
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai"+str(self.channel), min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)
        self.task.timing.cfg_samp_clk_timing(1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=2)
    def read_data(self):
        data = self.task.read(READ_ALL_AVAILABLE)
        return data
    def close(self):
        self.task.close()

   
