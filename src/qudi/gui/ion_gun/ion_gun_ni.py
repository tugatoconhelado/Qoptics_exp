import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE, VoltageUnits, Edge, FrequencyUnits, Level, WAIT_INFINITELY
import nidaqmx.constants
import nidaqmx.stream_readers
import numpy as np
from nidaqmx.stream_readers import AnalogMultiChannelReader
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
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai0:1", min_val=-10.0, max_val=10.0, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF, units=nidaqmx.constants.VoltageUnits.VOLTS)
        self.task.timing.cfg_samp_clk_timing(1000, sample_mode=AcquisitionType.FINITE,samps_per_chan=100)
        data = self.task.read(READ_ALL_AVAILABLE)
        datos=[]
        datos.append([data[0][0],data[1][0]])
        self.task.close()
        return datos

    def read_ctr_xy(self):
            self.taskAI = nidaqmx.Task()
            self.taskP = nidaqmx.Task()
            self.device = 'Dev1'
            self.samp_rate =1000
            self.samples = 100
            #Pulse Train
            self.taskP.co_channels.add_co_pulse_chan_freq(self.device + '/ctr0',
                                                    units = FrequencyUnits.HZ,
                                                    idle_state = Level.LOW,
                                                    initial_delay = 0.0,
                                                    freq = self.samp_rate,
                                                    duty_cycle = 0.5)

            self.taskP.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE,
                                            samps_per_chan = self.samples)
            
        #Analog Input
            self.taskAI.ai_channels.add_ai_voltage_chan(self.device + '/ai0:1',
                                                min_val=-10.0,
                                                max_val=10.0,
                                                units = VoltageUnits.VOLTS,
                                                terminal_config = nidaqmx.constants.TerminalConfiguration.DIFF)
            self.taskAI.timing.cfg_samp_clk_timing(self.samp_rate,
                                    'PFI4',
                                    active_edge = Edge.RISING,
                                    sample_mode = AcquisitionType.FINITE,
                                    samps_per_chan = self.samples)

            self.taskAI.start()
            self.taskP.start()
            data=np.zeros((2,self.samples),dtype=np.float64)
            Ar=nidaqmx.stream_readers.AnalogMultiChannelReader(self.taskAI.in_stream)

            Ar.read_many_sample(data,number_of_samples_per_channel=self.samples,timeout= 10)
            self.taskAI.wait_until_done()
            self.taskP.wait_until_done()
           
            self.taskAI.stop()
            self.taskP.stop()
            self.taskAI.close()
            self.taskP.close()
            datos=[]
            datos.append([data[0][0],data[1][0]])
            return data

   