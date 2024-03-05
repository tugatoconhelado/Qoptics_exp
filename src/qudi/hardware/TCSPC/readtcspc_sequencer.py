from ctypes import (
    CDLL, POINTER, c_char_p, c_bool, c_double, c_int,
    c_short, c_void_p, c_float, c_ushort, Structure,
    c_ulong, c_long, c_uint, c_uint64, byref
)
from qudi.hardware.TCSPC.spc_def import (
    SPCdata, SPCModInfo, SPC_EEP_Data, SPC_Adjust_Para,
    SPCMemConfig, PhotStreamInfo, PhotInfo, PhotInfo64,
    rate_values
)
import time
from qudi.hardware.TCSPC.tcspc import SPCDllWrapper
import os
import matplotlib.pyplot as plt

def test_state(tcspc, module_no, print_status=False):

    state_var = c_short()
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    #print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    status_code = tcspc.translate_status(state)
    if print_status:
        print(f'Status code: {status_code}')

    return status_code

def empty_memory_bank(tcspc, module_no, mem_info):

    status, mod_no, block, page, fill_value = tcspc.SPC_fill_memory(module_no, -1, -1, 1)
    #print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')
    continue_fill = True
    while continue_fill:
        status_code = test_state(tcspc, module_no)

        if 'SPC_HFILL_NRDY' in status_code:
            print('Memory bank not filled')
            time.sleep(1)
        else:
            continue_fill = False
            print('Memory bank filled')

def read_tcspc_sequencer():

    tcspc = SPCDllWrapper()

    ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\new_settings.ini')
    init_status, args = tcspc.SPC_init(ini_file_path)
    print(f'Init status: {init_status} with args: {args}')

    module_no = 0
    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mode, force_use, in_use = tcspc.SPC_set_mode(0, 1, 1)
    print(f'Get mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

    status, mod_no, adc_resolution, no_of_routing_bits, mem_info = tcspc.SPC_configure_memory(module_no, 10, 0, SPCMemConfig())
    print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
    no_of_blocks = mem_info.max_block_no

    page_no = 0
    # Reports on mem info
    red_factor = 1
    first_page = 0
    last_page = mem_info.maxpage - 1
    no_of_points = int(mem_info.block_length * mem_info.blocks_per_frame * mem_info.frames_per_page * (last_page - first_page + 1))
    print(f'Max block no: {mem_info.max_block_no}')
    print(f'Blocks per frame: {mem_info.blocks_per_frame}')
    print(f'Frames per page: {mem_info.frames_per_page}')
    print(f'Max page: {mem_info.maxpage}')
    print(f'Block length: {mem_info.block_length}')
    print(f'No of points: {no_of_points}')

    data_buffer = (c_ushort * no_of_points)()

    # Enables the sequencer
    status, mod_no, enable = tcspc.SPC_enable_sequencer(module_no, 1)
    print(f'Enable sequencer status: {status} with mod_no: {mod_no} and enable: {enable}')

    # Clears all blocks and pages of memory bank 0
    empty_memory_bank(tcspc, module_no, mem_info)

    # Switch to memory bank 1
    data.mem_bank = 1
    status, mod_no, data = tcspc.SPC_set_parameters(module_no, data)
    print(f'Set parameters status: {status} with mod_no: {mod_no} and data mem bank: {data.mem_bank}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data mem bank: {data.mem_bank}')


    iterate_memory_bank = True
    step_counter = 0
    no_of_steps = 3
    while iterate_memory_bank:

        # Clears all blocks and pages of memory bank 1
        empty_memory_bank(tcspc, module_no, mem_info)

        status_code = test_state(tcspc, module_no, True)

        # Starts the measurement
        status, mod_no = tcspc.SPC_start_measurement(module_no)
        print(f'Start measurement status: {status} with mod_no: {mod_no}')

        continue_acquisition = True

        while continue_acquisition:

            status_code = test_state(tcspc, module_no, True)

            if 'SPC_ARMED' not in status_code:
                continue_acquisition = False
                print('Block ready to be read')

            print('Sleeping for a sec')
            time.sleep(1)

        status, mod_no, block, page, reduction_factor, var_from, var_to, data = tcspc.SPC_read_data_block(module_no, 0, page_no, red_factor, 0, no_of_points - 1, data_buffer)
        print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
        print(f'Data list: {list(data_buffer)}')

        if step_counter == no_of_steps - 1:
            iterate_memory_bank = False
            print('Acquisition finished')
        else:
            step_counter += 1
    
    state_var = c_short()
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    status_code = tcspc.translate_status(state)
    print(f'Status code: {status_code}')

    if 'SPC_ARMED' not in status_code:
        status, mod_no, block, page, reduction_factor, var_from, var_to, data = tcspc.SPC_read_data_block(module_no, 0, page_no, red_factor, 0, no_of_points - 1, data_buffer)
        print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
        print(f'Data list: {list(data_buffer)}')

    plt.plot(data_buffer)
    plt.show()
   

if __name__ == '__main__':
    read_tcspc_sequencer()