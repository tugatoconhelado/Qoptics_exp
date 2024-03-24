from ctypes import (
    CDLL, POINTER, c_char_p, c_bool, c_double, c_int,
    c_short, c_void_p, c_float, c_ushort, Structure,
    c_ulong, c_long, c_uint, c_uint64, byref
)
from qudi.hardware.tcspc.spc_def import (
    SPCdata, SPCModInfo, SPC_EEP_Data, SPC_Adjust_Para,
    SPCMemConfig, PhotStreamInfo, PhotInfo, PhotInfo64,
    rate_values
)
import time
from qudi.hardware.tcspc.tcspc import SPCDllWrapper
import os
import matplotlib.pyplot as plt
import copy
import numpy as np


class TCSPCReader:


    def __init__(self) -> None:
        
        self.module_no = 0
        self.current_mode = 0
        self.initialise_tcspc()

    def initialise_tcspc(self):

        self.tcspc_wrapper = SPCDllWrapper()

        ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\spcm_test.ini')
        init_status, args = self.tcspc_wrapper.SPC_init(ini_file_path)
        print(f'Init status: {init_status} with args: {args}')

        init_status, args = self.tcspc_wrapper.SPC_get_init_status(self.module_no)
        print(f'Init status of module {self.module_no}: {init_status} with args: {args}')

        status, mode, force_use, in_use = self.tcspc_wrapper.SPC_set_mode(130, 1, 1)
        print(f'Set mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

        init_status, args = self.tcspc_wrapper.SPC_get_init_status(self.module_no)
        print(f'Init status of module {self.module_no}: {init_status} with args: {args}')

        status, mod_no, data = self.tcspc_wrapper.SPC_get_parameters(self.module_no)
        print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

        self.tcspc_parameters = data

        return self.tcspc_wrapper
    
    def set_normal_mode(self, module_no=0):

        status, mod_no, par_id, self.current_mode = self.tcspc_wrapper.SPC_get_parameter(module_no, 27, 0)
        print(f'Get parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {self.current_mode}')

        print(f'Current mode: {self.current_mode}')

    def configure_memory(self, module_no, page_no=1):

        status, mod_no, adc_resolution, no_of_routing_bits, mem_info = self.tcspc_wrapper.SPC_configure_memory(module_no, 10, 0, SPCMemConfig())
        print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
        self.tcspc_mem_info = mem_info

        status, mod_no, page = self.tcspc_wrapper.SPC_set_page(module_no, page_no)
        print(f'Set page status: {status} with mod_no: {mod_no} and page: {page}')

        status, mod_no, enable = self.tcspc_wrapper.SPC_enable_sequencer(module_no, 0)
        print(f'Enable sequencer status: {status} with mod_no: {mod_no} and enable: {enable}')

        return mem_info
        
    def empty_memory_bank(self, module_no, block, page_no, fill_value):

        status, mod_no, block, page, fill_value = self.tcspc_wrapper.SPC_fill_memory(module_no, block, page_no, fill_value)
        print(f'Fill memory status: {status} with mod_no: {mod_no}, block: {block}, page: {page} and fill_value: {fill_value}')
        continue_fill = True
        while continue_fill:
            status_code = self.test_state(module_no)

            if 'SPC_HFILL_NRDY' in status_code:
                print('Memory bank not filled')
                time.sleep(1)
            else:
                continue_fill = False
                print('Memory bank filled')

    def test_state(self, module_no, print_status=False):

        state_var = 0
        status, mod_no, state = self.tcspc_wrapper.SPC_test_state(module_no, state_var)
        #print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
        status_code = self.tcspc_wrapper.translate_status(state)
        if print_status:
            print(f'Status code: {status_code}')

        return status_code

    def start_single_mode_measurement(self, module_no, page_no):

        self.module_no = module_no
        self.measurement_page = page_no

        self.set_normal_mode(self.module_no)
        self.configure_memory(-1, self.measurement_page)
        print(self.tcspc_mem_info.maxpage)

        self.empty_memory_bank(-1, -1, self.measurement_page, 1)

        self.no_of_points = 1024
        self.data_buffer = (c_ushort * self.no_of_points)()

        status, mod_no = self.tcspc_wrapper.SPC_start_measurement(module_no)
        print(f'Start single mode measurement status: {status} with mod_no: {mod_no}')

        self.continue_acquisition = True
        self.measure()

    def measure(self):

        while self.continue_acquisition:

            state = self.test_state(self.module_no, True)
            
            #status, mod_no, block, page, reduction_factor, var_from, var_to, data = self.tcspc_wrapper.SPC_read_data_block(self.module_no, 0, 0, 1, 0, 1024 - 1, self.data_buffer)
            #print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
            #print(f'Data list: {np.mean(list(data))}')

            #status, mod_no, first_page, last_page, data = self.tcspc_wrapper.SPC_read_data_page(self.module_no, 0, 1, self.data_buffer)
            #print(f'Read data page status: {status} with mod_no: {mod_no}, first_page: {first_page}, last_page: {last_page} and data: {data}')
            #print(f'Data list: {list(data)}')
            
            status, mod_no, frame, page, data = self.tcspc_wrapper.SPC_read_data_frame(self.module_no, 0, 0, self.data_buffer)
            print(f'Read data frame status: {status} with mod_no: {mod_no}, frame: {frame}, page: {page} and data: {data}')
            print(f'Data list: {list(data)}')

            if 'SPC_TIME_OVER' in state:
                self.continue_acquisition = False
                print('Acquisition finished')
                break
            time.sleep(1)


if __name__ == '__main__':

    reader = TCSPCReader()
    reader.start_single_mode_measurement(0, 0)