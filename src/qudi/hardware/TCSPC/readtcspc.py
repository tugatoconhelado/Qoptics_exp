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

def test_state(tcspc, module_no, print_status=False):

    state_var = 0
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    #print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    status_code = tcspc.translate_status(state)
    if print_status:
        print(f'Status code: {status_code}')

    return status_code

def empty_memory_bank(tcspc, module_no):

    status, mod_no, block, page, fill_value = tcspc.SPC_fill_memory(module_no, 0, 1, 1)
    print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')
    continue_fill = True
    #while continue_fill:
    #    status_code = test_state(tcspc, module_no)

        #if 'SPC_HFILL_NRDY' in status_code:
        #    print('Memory bank not filled')
        #    time.sleep(1)
        #else:
        #    continue_fill = False
        #    print('Memory bank filled')


def initialise_tcspc():

    tcspc = SPCDllWrapper()

    ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\spcm_test.ini')
    init_status, args = tcspc.SPC_init(ini_file_path)
    print(f'Init status: {init_status} with args: {args}')

    module_no = 0
    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mode, force_use, in_use = tcspc.SPC_set_mode(0, 1, 1)
    print(f'Set mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

    return tcspc


def configure_memory(tcspc, module_no, page_no=1):

    status, mod_no, adc_resolution, no_of_routing_bits, mem_info = tcspc.SPC_configure_memory(module_no, 10, 0, SPCMemConfig())
    print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
    no_of_blocks = mem_info.max_block_no

    status, mod_no, page = tcspc.SPC_set_page(module_no, page_no)
    print(f'Set page status: {status} with mod_no: {mod_no} and page: {page}')

    status, mod_no, enable = tcspc.SPC_enable_sequencer(module_no, 0)
    print(f'Enable sequencer status: {status} with mod_no: {mod_no} and enable: {enable}')

    return mem_info

tcspc = initialise_tcspc()
#tcspc = SPCDllWrapper()
module_no = 0
mem_info = configure_memory(tcspc, module_no)
empty_memory_bank(tcspc, module_no)

red_factor = 1
#no_of_points = int(mem_info.block_length / red_factor)
#print(f'Max block no: {mem_info.max_block_no}')
#print(f'Blocks per frame: {mem_info.blocks_per_frame}')
#print(f'Frames per page: {mem_info.frames_per_page}')
#print(f'Max page: {mem_info.maxpage}')
#print(f'Block length: {mem_info.block_length}')
#print(f'No of points: {no_of_points}')
no_of_points = 1024
data_buffer = (c_ushort * no_of_points)()

status, mod_no = tcspc.SPC_start_measurement(module_no)
print(f'Start measurement status: {status} with mod_no: {mod_no}')

continue_acquisition = True
counter = 0
#state_var = c_short()
#status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
#print(f'State var: {bin(state_var.value)}')
#status_code = tcspc.translate_status(state)
#print(f'Status code: {status_code}')

while continue_acquisition:

    state_var = c_short()
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    print(f'State var: {status}')
    status_code = tcspc.translate_status(state)
    print(f'Status code: {status_code}')
    data_buffer = (c_ushort * no_of_points)()

    status = 12

    status, mod_no, block, page, reduction_factor, var_from, var_to, data = tcspc.SPC_read_data_block(module_no, 0, 0, red_factor, 0, no_of_points - 1, data_buffer)
    time.sleep(1)
    print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
    print(f'Data list: {np.mean(list(data_buffer))}')
    

    #status, mod_no, first_page, last_page, data = tcspc.SPC_read_data_page(module_no, 0, 4097, data_buffer)
    #print(f'Read data page status: {status} with mod_no: {mod_no}, first_page: {first_page}, last_page: {last_page} and data: {data}')
    #print(f'Data list: {list(data_buffer)}')

    #status, mod_no, frame, page, data = tcspc.SPC_read_data_frame(module_no, 0, 0, data_buffer)
    #print(f'Read data frame status: {status} with mod_no: {mod_no}, frame: {frame}, page: {page} and data: {data}')
    #print(f'Data list: {list(data_buffer)}')

    #if 'SPC_TIME_OVER' in status_code:
    #    continue_acquisition = False
    #    print('Acquisition finished')

    print('Sleeping for a sec')
    
    counter += 1
    if counter == 5:
        continue_acquisition = False

#plt.plot(data)
#plt.show()
        