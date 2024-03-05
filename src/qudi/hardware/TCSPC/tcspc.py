"""
Contains the TCSPS class to control Becker & Hickl SPC130-EM
"""
import os
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


class SPCDllWrapper:
    

    def __init__(self) -> None:
        
        self.__dll = CDLL(os.path.abspath('C:\Program Files (x86)\BH\SPCM\DLL\spcm64.dll'))

        # Initialisation functions
        self.__SPC_init = self.__dll.SPC_init
        self.__SPC_init.restype = c_short
        self.__SPC_init.argtypes = [c_char_p]

        self.__SPC_get_init_status = self.__dll.SPC_get_init_status
        self.__SPC_get_init_status.restype = c_short
        self.__SPC_get_init_status.argtypes = [c_short]

        self.__SPC_get_module_info = self.__dll.SPC_get_module_info
        self.__SPC_get_module_info.restype = c_short
        self.__SPC_get_module_info.argtypes = [c_int, POINTER(SPCModInfo)] # This should be a pointer to a structure of SPCModInfo
        
        self.__SPC_test_id = self.__dll.SPC_test_id
        self.__SPC_test_id.restype = c_short
        self.__SPC_test_id.argtypes = [c_short]

        self.__SPC_set_mode = self.__dll.SPC_set_mode
        self.__SPC_set_mode.restype = c_short
        self.__SPC_set_mode.argtypes = [c_short, c_short, POINTER(c_int)]

        self.__SPC_get_mode = self.__dll.SPC_get_mode
        self.__SPC_get_mode.restype = c_short
        self.__SPC_get_mode.argtypes = [c_void_p]

        # Setup functions
        self.__SPC_get_parameters = self.__dll.SPC_get_parameters
        self.__SPC_get_parameters.restype = c_short
        self.__SPC_get_parameters.argtypes = [c_short, POINTER(SPCdata)]

        self.__SPC_set_parameters = self.__dll.SPC_set_parameters
        self.__SPC_set_parameters.restype = c_short
        self.__SPC_set_parameters.argtypes = [c_short, POINTER(SPCdata)]

        self.__SPC_get_parameter = self.__dll.SPC_get_parameter
        self.__SPC_get_parameter.restype = c_short
        self.__SPC_get_parameter.argtypes = [c_short, c_short, POINTER(c_float)]

        self.__SPC_set_parameter = self.__dll.SPC_set_parameter
        self.__SPC_set_parameter.restype = c_short
        self.__SPC_set_parameter.argtypes = [c_short, c_short, c_float]

        self.__SPC_get_eeprom_data = self.__dll.SPC_get_eeprom_data
        self.__SPC_get_eeprom_data.restype = c_short
        self.__SPC_get_eeprom_data.argtypes = [c_short, POINTER(SPC_EEP_Data)]

        self.__SPC_write_eeprom_data = self.__dll.SPC_write_eeprom_data
        self.__SPC_write_eeprom_data.restype = c_short
        self.__SPC_write_eeprom_data.argtypes = [c_short, c_ushort, POINTER(SPC_EEP_Data)]

        self.__SPC_get_adjust_parameters = self.__dll.SPC_get_adjust_parameters
        self.__SPC_get_adjust_parameters.restype = c_short
        self.__SPC_get_adjust_parameters.argtypes = [c_short, POINTER(SPC_Adjust_Para)]

        self.__SPC_set_adjust_parameters = self.__dll.SPC_set_adjust_parameters
        self.__SPC_set_adjust_parameters.restype = c_short
        self.__SPC_set_adjust_parameters.argtypes = [c_short, POINTER(SPC_Adjust_Para)]

        self.__SPC_read_parameters_from_inifile = self.__dll.SPC_read_parameters_from_inifile
        self.__SPC_read_parameters_from_inifile.restype = c_short
        self.__SPC_read_parameters_from_inifile.argtypes = [POINTER(SPCdata), c_char_p]

        self.__SPC_save_parameters_to_inifile = self.__dll.SPC_save_parameters_to_inifile
        self.__SPC_save_parameters_to_inifile.restype = c_short
        self.__SPC_save_parameters_to_inifile.argtypes = [POINTER(SPCdata), c_char_p, c_char_p, c_int]


        # Status functions
        self.__SPC_test_state = self.__dll.SPC_test_state
        self.__SPC_test_state.restype = c_short
        self.__SPC_test_state.argtypes = [c_short, POINTER(c_short)]

        self.__SPC_get_sync_state = self.__dll.SPC_get_sync_state
        self.__SPC_get_sync_state.restype = c_short
        self.__SPC_get_sync_state.argtypes = [c_short, POINTER(c_short)]

        self.__SPC_get_time_from_start = self.__dll.SPC_get_time_from_start
        self.__SPC_get_time_from_start.restype = c_short
        self.__SPC_get_time_from_start.argtypes = [c_short, POINTER(c_float)]

        self.__SPC_get_break_time = self.__dll.SPC_get_break_time
        self.__SPC_get_break_time.restype = c_short
        self.__SPC_get_break_time.argtypes = [c_short, POINTER(c_float)]

        self.__SPC_get_actual_coltime = self.__dll.SPC_get_actual_coltime
        self.__SPC_get_actual_coltime.restype = c_short
        self.__SPC_get_actual_coltime.argtypes = [c_short, POINTER(c_float)]

        self.__SPC_read_rates = self.__dll.SPC_read_rates
        self.__SPC_read_rates.restype = c_short
        self.__SPC_read_rates.argtypes = [c_short, POINTER(rate_values)]

        self.__SPC_clear_rates = self.__dll.SPC_clear_rates
        self.__SPC_clear_rates.restype = c_short
        self.__SPC_clear_rates.argtypes = [c_short]

        self.__SPC_get_sequencer_state = self.__dll.SPC_get_sequencer_state
        self.__SPC_get_sequencer_state.restype = c_short
        self.__SPC_get_sequencer_state.argtypes = [c_short, POINTER(c_short)]
        
        self.__SPC_read_gap_time = self.__dll.SPC_read_gap_time
        self.__SPC_read_gap_time.restype = c_short
        self.__SPC_read_gap_time.argtypes = [c_short, POINTER(c_float)]

        self.__SPC_get_scan_clk_state = self.__dll.SPC_get_scan_clk_state
        self.__SPC_get_scan_clk_state.restype = c_short
        self.__SPC_get_scan_clk_state.argtypes = [c_short, POINTER(c_short)]

        self.__SPC_get_fifo_usage = self.__dll.SPC_get_fifo_usage
        self.__SPC_get_fifo_usage.restype = c_short
        self.__SPC_get_fifo_usage.argtypes = [c_short, POINTER(c_float)]

        # Measurement control functions
        self.__SPC_start_measurement = self.__dll.SPC_start_measurement
        self.__SPC_start_measurement.restype = c_short
        self.__SPC_start_measurement.argtypes = [c_short]

        self.__SPC_pause_measurement = self.__dll.SPC_pause_measurement
        self.__SPC_pause_measurement.restype = c_short
        self.__SPC_pause_measurement.argtypes = [c_short]

        self.__SPC_restart_measurement = self.__dll.SPC_restart_measurement
        self.__SPC_restart_measurement.restype = c_short
        self.__SPC_restart_measurement.argtypes = [c_short]

        self.__SPC_stop_measurement = self.__dll.SPC_stop_measurement
        self.__SPC_stop_measurement.restype = c_short
        self.__SPC_stop_measurement.argtypes = [c_short]

        self.__SPC_set_page = self.__dll.SPC_set_page
        self.__SPC_set_page.restype = c_short
        self.__SPC_set_page.argtypes = [c_short, c_long]

        self.__SPC_enable_sequencer = self.__dll.SPC_enable_sequencer
        self.__SPC_enable_sequencer.restype = c_short
        self.__SPC_enable_sequencer.argtypes = [c_short, c_short]

        # SPC Memory transfer functions
        self.__SPC_configure_memory = self.__dll.SPC_configure_memory
        self.__SPC_configure_memory.restype = c_short
        self.__SPC_configure_memory.argtypes = [c_short, c_short, c_short, POINTER(SPCMemConfig)]

        self.__SPC_fill_memory = self.__dll.SPC_fill_memory
        self.__SPC_fill_memory.restype = c_short
        self.__SPC_fill_memory.argtypes = [c_short, c_long, c_long, c_ushort]

        self.__SPC_read_data_block = self.__dll.SPC_read_data_block
        self.__SPC_read_data_block.restype = c_short
        self.__SPC_read_data_block.argtypes = [c_short, c_long, c_long, c_short, c_short, c_short, POINTER(c_ushort)]

        self.__SPC_write_data_block = self.__dll.SPC_write_data_block
        self.__SPC_write_data_block.restype = c_short
        self.__SPC_write_data_block.argtypes = [c_short, c_long, c_long, c_short, c_short, POINTER(c_ushort)]

        self.__SPC_read_fifo = self.__dll.SPC_read_fifo
        self.__SPC_read_fifo.restype = c_short
        self.__SPC_read_fifo.argtypes = [c_short, POINTER(c_ulong), POINTER(c_ushort)]

        self.__SPC_read_data_frame = self.__dll.SPC_read_data_frame
        self.__SPC_read_data_frame.restype = c_short
        self.__SPC_read_data_frame.argtypes = [c_short, c_long, c_long, POINTER(c_ushort)]

        self.__SPC_read_data_page = self.__dll.SPC_read_data_page
        self.__SPC_read_data_page.restype = c_short
        self.__SPC_read_data_page.argtypes = [c_short, c_long, c_long, POINTER(c_ushort)]

        self.__SPC_read_block = self.__dll.SPC_read_block
        self.__SPC_read_block.restype = c_short
        self.__SPC_read_block.argtypes = [c_short, c_long, c_long, c_long, c_short, c_short, POINTER(c_ushort)]

        self.__SPC_save_data_to_sdtfile = self.__dll.SPC_save_data_to_sdtfile
        self.__SPC_save_data_to_sdtfile.restype = c_short
        self.__SPC_save_data_to_sdtfile.argtypes = [c_short, POINTER(c_ushort), c_ulong, c_char_p]

        # Functions to manage photon streams
        self.__SPC_init_phot_stream = self.__dll.SPC_init_phot_stream
        self.__SPC_init_phot_stream.restype = c_short
        self.__SPC_init_phot_stream.argtypes = [c_short, c_char_p, c_short, c_short, c_short]

        self.__SPC_get_phot_stream_info = self.__dll.SPC_get_phot_stream_info
        self.__SPC_get_phot_stream_info.restype = c_short
        self.__SPC_get_phot_stream_info.argtypes = [c_short, POINTER(PhotStreamInfo)]

        self.__SPC_get_photon = self.__dll.SPC_get_photon
        self.__SPC_get_photon.restype = c_short
        self.__SPC_get_photon.argtypes = [c_short, POINTER(PhotInfo)]

        self.__SPC_close_phot_stream = self.__dll.SPC_close_phot_stream
        self.__SPC_close_phot_stream.restype = c_short
        self.__SPC_close_phot_stream.argtypes = [c_short]

        self.__SPC_get_fifo_init_vars = self.__dll.SPC_get_fifo_init_vars
        self.__SPC_get_fifo_init_vars.restype = c_short
        self.__SPC_get_fifo_init_vars.argtypes = [c_short, POINTER(c_short), POINTER(c_short), POINTER(c_int), POINTER(c_uint)]

        self.__SPC_init_buf_stream = self.__dll.SPC_init_buf_stream
        self.__SPC_init_buf_stream.restype = c_short
        self.__SPC_init_buf_stream.argtypes = [c_short, c_short, c_short, c_int, c_uint]

        self.__SPC_add_data_to_stream = self.__dll.SPC_add_data_to_stream
        self.__SPC_add_data_to_stream.restype = c_short
        self.__SPC_add_data_to_stream.argtypes = [c_short, POINTER(c_void_p), c_uint]

        self.__SPC_read_fifo_to_stream = self.__dll.SPC_read_fifo_to_stream
        self.__SPC_read_fifo_to_stream.restype = c_short
        self.__SPC_read_fifo_to_stream.argtypes = [c_short, c_short, POINTER(c_long)]

        self.__SPC_get_photons_from_stream = self.__dll.SPC_get_photons_from_stream
        self.__SPC_get_photons_from_stream.restype = c_short
        self.__SPC_get_photons_from_stream.argtypes = [c_short, POINTER(PhotInfo), POINTER(c_int)] # This should be a pointer to a structure of PhotInfo64

        self.__SPC_stream_start_condition = self.__dll.SPC_stream_start_condition
        self.__SPC_stream_start_condition.restype = c_short
        self.__SPC_stream_start_condition.argtypes = [c_short, c_double, c_uint, c_uint]

        self.__SPC_stream_stop_condition = self.__dll.SPC_stream_stop_condition
        self.__SPC_stream_stop_condition.restype = c_short
        self.__SPC_stream_stop_condition.argtypes = [c_short, c_double, c_uint, c_uint]

        self.__SPC_stream_reset = self.__dll.SPC_stream_reset
        self.__SPC_stream_reset.restype = c_short
        self.__SPC_stream_reset.argtypes = [c_short]

        self.__SPC_get_stream_buffer_size = self.__dll.SPC_get_stream_buffer_size
        self.__SPC_get_stream_buffer_size.restype = c_short
        self.__SPC_get_stream_buffer_size.argtypes = [c_short, c_ushort, c_uint]

        self.__SPC_get_buffer_from_stream = self.__dll.SPC_get_buffer_from_stream
        self.__SPC_get_buffer_from_stream.restype = c_short
        self.__SPC_get_buffer_from_stream.argtypes = [c_short, c_ushort, POINTER(c_uint), c_char_p, c_short]

        # Other functions
        self.__SPC_get_error_string = self.__dll.SPC_get_error_string
        self.__SPC_get_error_string.restype = c_short
        self.__SPC_get_error_string.argtypes = [c_short, c_char_p, c_short]

        self.__SPC_get_detector_info = self.__dll.SPC_get_detector_info
        self.__SPC_get_detector_info.restype = c_short
        self.__SPC_get_detector_info.argtypes = [c_short, POINTER(c_short), c_char_p]

        self.__SPC_close = self.__dll.SPC_close
        self.__SPC_close.restype = c_short
        self.__SPC_close.argtypes = [c_void_p]

    def SPC_init(self, ini_file: str):

        print('Initialising with ini file: ', ini_file)
        arg1 = ini_file.encode('utf-8')
        ret = self.__SPC_init(arg1)
        return ret, ini_file
    
    def SPC_get_init_status(self, mod_no: int):
        arg1 = c_short(mod_no)
        ret = self.__SPC_get_init_status(arg1)
        return ret, arg1

    def SPC_set_mode(self, mode, force_use, in_use):

        arg1 = c_short(mode)
        arg2 = c_short(force_use)
        arg3 = c_int(in_use)
        ret = self.__SPC_set_mode(arg1, arg2, byref(arg3))
        return ret, arg1, arg2, arg3

    def SPC_get_parameters(self, mod_no: int):
        arg1 = c_short(mod_no)
        arg2 = SPCdata()
        ret = self.__SPC_get_parameters(arg1, arg2)
        return ret, arg1, arg2
    
    def SPC_get_parameter(self, mod_no: int, param_id: int):
        arg1 = c_short(mod_no)
        arg2 = c_short(param_id)
        arg3 = c_float()
        ret = self.__SPC_get_parameter(arg1, arg2, byref(arg3))
        return ret, arg1, arg2, arg3
    
    def SPC_set_parameters(self, mod_no: int, data: SPCdata):
        arg1 = c_short(mod_no)
        arg2 = data
        ret = self.__SPC_set_parameters(arg1, arg2)
        return ret, arg1, arg2
    
    def SPC_set_parameter(self, mod_no: int, param_id: int, value):
        arg1 = c_short(mod_no)
        arg2 = c_short(param_id)
        arg3 = c_float(value)
        ret = self.__SPC_set_parameter(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_read_parameters_from_inifile(self, data: SPCdata, ini_file: str):
        arg1 = data
        arg2 = ini_file.encode('utf-8')
        ret = self.__SPC_read_parameters_from_inifile(arg1, arg2)
        return ret, arg1, arg2
    
    def SPC_save_parameters_to_inifile(self, data: SPCdata, dest_ini_file: str, source_ini_file: str, with_comments: int):
        arg1 = data
        arg2 = dest_ini_file.encode('utf-8')
        arg3 = source_ini_file.encode('utf-8')
        arg4 = c_int(with_comments)
        ret = self.__SPC_save_parameters_to_inifile(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4

    def SPC_configure_memory(self, mod_no, adc_resolution, no_of_routing_bits, mem_info):

        arg1 = c_short(mod_no)
        arg2 = c_short(adc_resolution)
        arg3 = c_short(no_of_routing_bits)
        arg4 = mem_info
        ret = self.__SPC_configure_memory(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4
    
    def SPC_set_page(self, mod_no, page):

        arg1 = c_short(mod_no)
        arg2 = c_long(page)
        ret = self.__SPC_set_page(arg1, arg2)
        return ret, arg1, arg2

    def SPC_fill_memory(self, mod_no, block, page, fill_value):

        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(page)
        arg4 = c_ushort(fill_value)
        ret = self.__SPC_fill_memory(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4

    def SPC_start_measurement(self, mod_no):

        arg1 = c_short(mod_no)
        ret = self.__SPC_start_measurement(arg1)
        return ret, arg1

    def SPC_test_state(self, mod_no, state):

        arg1 = c_short(mod_no)
        arg2 = c_short(state)
        ret = self.__SPC_test_state(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_read_data_block(self, mod_no, block, page, reduction_factor, var_from, var_to, data):
            
        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(page)
        arg4 = c_short(reduction_factor)
        arg5 = c_short(var_from)
        arg6 = c_short(var_to)
        ret = self.__SPC_read_data_block(arg1, arg2, arg3, arg4, arg5, arg6, data)
        return ret, arg1, arg2, arg3, arg4, arg5, arg6, data

if __name__ == '__main__':

    print(SPCdata)
    print('hola mundo')
    tcspc = SPCDllWrapper()

    #ini_file_path = os.path.abspath('C:\Program Files (x86)\BH\SPCM\spcm.ini')
    ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\spcm_test.ini')
    init_status, args = tcspc.SPC_init(ini_file_path)
    print(f'Init status: {init_status} with args: {args}')

    status, mode, force_use, in_use = tcspc.SPC_set_mode(130, 1, 1)
    print(f'Get mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

    module_no = 0
    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data: {data.cfd_zc_level}')

    # Parameter Read write test
    #data.cfd_zc_level = -5.29
    #print(f'Setting cfd_zc_level to {data.cfd_zc_level}')

    #status, mod_no, data = tcspc.SPC_set_parameters(module_no, data)
    #print(f'Set parameters status: {status} with mod_no: {mod_no} and data: {data.cfd_zc_level}')

    #status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    #print(f'Get parameters status: {status} with mod_no: {mod_no} and data: {data.cfd_zc_level}')

    #status, mod_no, param_id, value = tcspc.SPC_get_parameter(module_no, 2)
    #print(f'Get parameter status: {status} with mod_no: {mod_no}, param_id: {param_id} and value: {value}')

    #status, mod_no, param_id, value = tcspc.SPC_set_parameter(module_no, 2, 0.0)
    #print(f'Set parameter status: {status} with mod_no: {mod_no}, param_id: {param_id} and value: {value}')

    #status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    #print(f'Get parameters status: {status} with mod_no: {mod_no} and data: {data.cfd_zc_level}')

    #status, mod_no, param_id, value = tcspc.SPC_get_parameter(module_no, 2)
    #print(f'Get parameter status: {status} with mod_no: {mod_no}, param_id: {param_id} and value: {value}')

    #status, mod_no, param_id, value = tcspc.SPC_set_parameter(module_no, 2, -5.3)
    #print(f'Set parameter status: {status} with mod_no: {mod_no}, param_id: {param_id} and value: {value}')

    #status, mod_no, param_id, value = tcspc.SPC_get_parameter(module_no, 2)
    #print(f'Get parameter status: {status} with mod_no: {mod_no}, param_id: {param_id} and value: {value}')

    #status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    #print(f'Get parameters status: {status} with mod_no: {mod_no} and data: {data.cfd_zc_level}')

    # Read from file
    #status, data, ini_file = tcspc.SPC_read_parameters_from_inifile(data, ini_file_path)
    #print(f'Read parameters from ini file status: {status} with data: {data} and ini_file: {ini_file}')
    #print(f'cfd_zc_level: {data.cfd_zc_level}')

    #test_ini_file = os.path.abspath('C:\EXP\python\Qoptics_exp\spcm_test.ini')

    # Save to file
    #status, data, dest_ini_file, source_ini_file, with_comments = tcspc.SPC_save_parameters_to_inifile(data, test_ini_file, ini_file_path, 0)
    #print(f'Save parameters to ini file status: {status} with data: {data}, dest_ini_file: {dest_ini_file}, source_ini_file: {source_ini_file} and with_comments: {with_comments}')

    status, mod_no, adc_resolution, no_of_routing_bits, mem_info = tcspc.SPC_configure_memory(module_no, 10, 3, SPCMemConfig())
    print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
    no_of_blocks = mem_info.max_block_no

    status, mod_no, page = tcspc.SPC_set_page(module_no, 0)
    print(f'Set page status: {status} with mod_no: {mod_no} and page: {page}')

    status, block, mod_no, page, fill_value = tcspc.SPC_fill_memory(module_no, 0, 0, 0)
    print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')

    status, mod_no = tcspc.SPC_start_measurement(module_no)
    print(f'Start measurement status: {status} with mod_no: {mod_no}')

    state_var = 0
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')

    status, mod_no, block, page, reduction_factor, var_from, var_to, data = tcspc.SPC_read_data_block(module_no, 0, 0, 1, 0, 0, c_ushort(0))
    print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')



    