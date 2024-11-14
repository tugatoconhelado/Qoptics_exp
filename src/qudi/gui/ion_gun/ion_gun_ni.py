import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE
import nidaqmx.constants
class myni:
    def __init__(self):
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai0", min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF, units=nidaqmx.constants.VoltageUnits.VOLTS)
        self.task.timing.cfg_samp_clk_timing(1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=2)
    def read_data(self):
        data = self.task.read(READ_ALL_AVAILABLE)
        return data
    def close(self):
        self.task.close()

    def read_xy(self):
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai0", min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF, units=nidaqmx.constants.VoltageUnits.VOLTS)
        self.task.timing.cfg_samp_clk_timing(1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=2)
        data = self.task.read(READ_ALL_AVAILABLE)
        datos=[]
        datos.append(data[0])
        self.task.close()
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai1", min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF, units=nidaqmx.constants.VoltageUnits.VOLTS)
        self.task.timing.cfg_samp_clk_timing(1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=2)
        data2 = self.task.read(READ_ALL_AVAILABLE)
        datos.append(data2[0])
        self.task.close()
        return datos