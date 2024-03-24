"""
Contains the TCSPS class to control Becker & Hickl SPC130-EM
"""
import os
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


   # Initialisation functions

    def SPC_init(self, ini_file: str):

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

    def SPC_get_mode(self):
        arg1 = c_int()
        ret = self.__SPC_get_mode(byref(arg1))
        return ret, arg1

   # Setup functions

    def SPC_get_parameters(self, mod_no: int, SPC_data: SPCdata = SPCdata()):
        arg1 = c_short(mod_no)
        arg2 = SPC_data
        ret = self.__SPC_get_parameters(arg1, arg2)
        return ret, arg1, arg2

    def SPC_set_parameters(self, mod_no: int, SPC_data: SPCdata):
        arg1 = c_short(mod_no)
        arg2 = SPC_data
        ret = self.__SPC_set_parameters(arg1, arg2)
        return ret, arg1, arg2

    def SPC_get_parameter(self, mod_no: int, param_id: int, value: float):
        arg1 = c_short(mod_no)
        arg2 = c_short(param_id)
        arg3 = c_float(value)
        ret = self.__SPC_get_parameter(arg1, arg2, byref(arg3))
        return ret, arg1, arg2, arg3
    
    def SPC_set_parameter(self, mod_no: int, param_id: int, value):
        arg1 = c_short(mod_no)
        arg2 = c_short(param_id)
        arg3 = c_float(value)
        ret = self.__SPC_set_parameter(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3

    def SPC_get_eeprom_data(self, mod_no, eep_data):

        arg1 = c_short(mod_no)
        arg2 = eep_data
        ret = self.__SPC_get_eeprom_data(arg1, arg2)
        return ret, arg1, arg2

    def SPC_write_eeprom_data(self, mod_no, write_enable, eep_data):
            
        arg1 = c_short(mod_no)
        arg2 = c_ushort(write_enable)
        arg3 = eep_data
        ret = self.__SPC_write_eeprom_data(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3

    def SPC_get_adjust_parameters(self, mod_no, adjpara):
            
        arg1 = c_short(mod_no)
        arg2 = adjpara
        ret = self.__SPC_get_adjust_parameters(arg1, arg2)
        return ret, arg1, arg2

    def SPC_set_adjust_parameters(self, mod_no, adjpara):
                    
        arg1 = c_short(mod_no)
        arg2 = adjpara
        ret = self.__SPC_set_adjust_parameters(arg1, arg2)
        return ret, arg1, arg2

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

   # Status functions

    def SPC_test_state(self, mod_no, state):

        arg1 = c_short(mod_no)
        arg2 = c_short(0)
        ret = self.__SPC_test_state(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_get_sync_state(self, mod_no, sync_state):
            
        arg1 = c_short(mod_no)
        arg2 = c_short(sync_state)
        ret = self.__SPC_get_sync_state(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_get_time_from_start(self, mod_no, time):
            
        arg1 = c_short(mod_no)
        arg2 = c_float(time)
        ret = self.__SPC_get_time_from_start(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_get_break_time(self, mod_no, time):
                
        arg1 = c_short(mod_no)
        arg2 = c_float(time)
        ret = self.__SPC_get_break_time(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_get_actual_coltime(self, mod_no, time):
                        
        arg1 = c_short(mod_no)
        arg2 = c_float(time)
        ret = self.__SPC_get_actual_coltime(arg1, byref(arg2))
        return ret, arg1, arg2

    def SPC_read_rates(self, mod_no, rate_values):

        arg1 = c_short(mod_no)
        arg2 = rate_values
        ret = self.__SPC_read_rates(arg1, arg2)
        return ret, arg1, arg2

    def SPC_clear_rates(self, mod_no):
            
        arg1 = c_short(mod_no)
        ret = self.__SPC_clear_rates(arg1)
        return ret, arg1

    def SPC_get_sequencer_state(self, mod_no, state):
                    
        arg1 = c_short(mod_no)
        arg2 = c_short(state)
        ret = self.__SPC_get_sequencer_state(arg1, byref(arg2))
        return ret, arg1, arg2
    
    def SPC_read_gap_time(self, mod_no, time):
    
        arg1 = c_short(mod_no)
        arg2 = c_float(time)
        ret = self.__SPC_read_gap_time(arg1, byref(arg2))
        return ret, arg1, arg2
    
    def SPC_get_scan_clk_state(self, mod_no, scan_state):
            
        arg1 = c_short(mod_no)
        arg2 = c_short(scan_state)
        ret = self.__SPC_get_scan_clk_state(arg1, byref(arg2))
        return ret, arg1, arg2
    
    def SPC_get_fifo_usage(self, mod_no, usage_degree):
                    
        arg1 = c_short(mod_no)
        arg2 = c_float(usage_degree)
        ret = self.__SPC_get_fifo_usage(arg1, byref(arg2))
        return ret, arg1, arg2

   # Measurement control functions

    def SPC_start_measurement(self, mod_no):

        arg1 = c_short(mod_no)
        ret = self.__SPC_start_measurement(arg1)
        return ret, arg1
    
    def SPC_pause_measurement(self, mod_no):
            
        arg1 = c_short(mod_no)
        ret = self.__SPC_pause_measurement(arg1)
        return ret, arg1
    
    def SPC_restart_measurement(self, mod_no):
                
        arg1 = c_short(mod_no)
        ret = self.__SPC_restart_measurement(arg1)
        return ret, arg1
    
    def SPC_stop_measurement(self, mod_no):

        arg1 = c_short(mod_no)
        ret = self.__SPC_stop_measurement(arg1)
        return ret, arg1

    def SPC_set_page(self, mod_no, page):

        arg1 = c_short(mod_no)
        arg2 = c_long(page)
        ret = self.__SPC_set_page(arg1, arg2)
        return ret, arg1, arg2

    def SPC_enable_sequencer(self, mod_no, enable):

        arg1 = c_short(mod_no)
        arg2 = c_short(enable)
        ret = self.__SPC_enable_sequencer(arg1, arg2)
        return ret, arg1, arg2

   # SPC Memory transfer functions

    def SPC_configure_memory(self, mod_no, adc_resolution, no_of_routing_bits, mem_info):

        arg1 = c_short(mod_no)
        arg2 = c_short(adc_resolution)
        arg3 = c_short(no_of_routing_bits)
        arg4 = mem_info
        ret = self.__SPC_configure_memory(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4
    
    def SPC_fill_memory(self, mod_no, block, page, fill_value):

        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(page)
        arg4 = c_ushort(fill_value)
        ret = self.__SPC_fill_memory(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4

    def SPC_read_data_block(self, mod_no, block, page, reduction_factor, var_from, var_to, data):
            
        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(page)
        arg4 = c_short(reduction_factor)
        arg5 = c_short(var_from)
        arg6 = c_short(var_to)
        ret = self.__SPC_read_data_block(arg1, arg2, arg3, arg4, arg5, arg6, data)
        return ret, arg1, arg2, arg3, arg4, arg5, arg6, data

    def SPC_write_data_block(self, mod_no, block, page, var_from, var_to, data):

        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(page)
        arg4 = c_short(var_from)
        arg5 = c_short(var_to)
        ret = self.__SPC_write_data_block(arg1, arg2, arg3, arg4, arg5, data)
        return ret, arg1, arg2, arg3, arg4, arg5, data

    def SPC_read_fifo(self, mod_no, count, data):

        arg1 = c_short(mod_no)
        arg2 = c_ulong(count)
        arg3 = data
        ret = self.__SPC_read_fifo(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3

    def SPC_read_data_frame(self, mod_no, frame, page, data):
                
        arg1 = c_short(mod_no)
        arg2 = c_long(frame)
        arg3 = c_long(page)
        ret = self.__SPC_read_data_frame(arg1, arg2, arg3, data)
        return ret, arg1, arg2, arg3, data

    def SPC_read_data_page(self, mod_no, first_page, last_page, data):
            
        arg1 = c_short(mod_no)
        arg2 = c_long(first_page)
        arg3 = c_long(last_page)
        ret = self.__SPC_read_data_page(arg1, arg2, arg3, data)
        return ret, arg1, arg2, arg3, data
    
    def SPC_read_block(self, mod_no, block, frame, page, var_from, var_to, data):

        arg1 = c_short(mod_no)
        arg2 = c_long(block)
        arg3 = c_long(frame)
        arg4 = c_long(page)
        arg5 = c_short(var_from)
        arg6 = c_short(var_to)
        ret = self.__SPC_read_block(arg1, arg2, arg3, arg4, arg5, arg6, data)
        return ret, arg1, arg2, arg3, arg4, arg5, arg6, data
  
    def SPC_save_data_to_sdtfile(self, mod_no, data_buf, bytes_no, sdt_file):

        arg1 = c_short(mod_no)
        arg2 = data_buf
        arg3 = c_ulong(bytes_no)
        arg4 = sdt_file.encode('utf-8')
        ret = self.__SPC_save_data_to_sdtfile(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4

   # Functions to manage photon streams
    
    def SPC_init_phot_stream(self, fifo_type, spc_file, files_to_use, stream_type, what_to_read):

        arg1 = c_short(fifo_type)
        arg2 = spc_file.encode('utf-8')
        arg3 = c_short(files_to_use)
        arg4 = c_short(stream_type)
        arg5 = c_short(what_to_read)
        ret = self.__SPC_init_phot_stream(arg1, arg2, arg3, arg4, arg5)
        return ret, arg1, arg2, arg3, arg4, arg5
    
    def SPC_get_phot_stream_info(self, stream_hndl, stream_info):

        arg1 = c_short(stream_hndl)
        arg2 = stream_info
        ret = self.__SPC_get_phot_stream_info(arg1, arg2)
        return ret, arg1, arg2

    def SPC_get_photon(self, stream_hndl, phot_info):

        arg1 = c_short(stream_hndl)
        arg2 = phot_info
        ret = self.__SPC_get_photon(arg1, arg2)
        return ret, arg1, arg2

    def SPC_close_phot_stream(self, stream_hndl):

        arg1 = c_short(stream_hndl)
        ret = self.__SPC_close_phot_stream(arg1)
        return ret, arg1
    
    def SPC_get_fifo_init_vars(self, mod_no, fifo_type, stream_type, mt_clock, spc_header):

        arg1 = c_short(mod_no)
        arg2 = c_short(fifo_type)
        arg3 = c_short(stream_type)
        arg4 = c_int(mt_clock)
        arg5 = c_uint(spc_header)
        ret = self.__SPC_get_fifo_init_vars(arg1, arg2, arg3, arg4, arg5)
        return ret, arg1, arg2, arg3, arg4, arg5
    
    def SPC_init_buf_stream(self, fifo_type, stream_type, what_to_read, mt_clock, start01_offfs):

        arg1 = c_short(fifo_type)
        arg2 = c_short(stream_type)
        arg3 = c_short(what_to_read)
        arg4 = c_int(mt_clock)
        arg5 = c_uint(start01_offfs)
        ret = self.__SPC_init_buf_stream(arg1, arg2, arg3, arg4, arg5)
        return ret, arg1, arg2, arg3, arg4, arg5

    def SPC_add_data_to_stream(self, stream_hndl, buffer, bytes_no):

        arg1 = c_short(stream_hndl)
        arg2 = buffer
        arg3 = c_uint(bytes_no)
        ret = self.__SPC_add_data_to_stream(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_read_fifo_to_stream(self, stream_hndl, mod_no, count):

        arg1 = c_short(stream_hndl)
        arg2 = c_short(mod_no)
        arg3 = c_long(count)
        ret = self.__SPC_read_fifo_to_stream(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_get_photons_from_stream(self, stream_hndl, phot_info, phot_no):

        arg1 = c_short(stream_hndl)
        arg2 = phot_info
        arg3 = c_int(phot_no)
        ret = self.__SPC_get_photons_from_stream(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_stream_start_condition(self, stream_hndl, start_time, start_OR_mask, start_AND_mask):

        arg1 = c_short(stream_hndl)
        arg2 = c_double(start_time)
        arg3 = c_uint(start_OR_mask)
        arg4 = c_uint(start_AND_mask)
        ret = self.__SPC_stream_start_condition(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4
    
    def SPC_stream_stop_condition(self, stream_hndl, stop_time, stop_OR_mask, stop_AND_mask):

        arg1 = c_short(stream_hndl)
        arg2 = c_double(stop_time)
        arg3 = c_uint(stop_OR_mask)
        arg4 = c_uint(stop_AND_mask)
        ret = self.__SPC_stream_stop_condition(arg1, arg2, arg3, arg4)
        return ret, arg1, arg2, arg3, arg4
    
    def SPC_stream_reset(self, stream_hndl):

        arg1 = c_short(stream_hndl)
        ret = self.__SPC_stream_reset(arg1)
        return ret, arg1
    
    def SPC_get_stream_buffer_size(self, stream_hndl, buf_no, buf_size):

        arg1 = c_short(stream_hndl)
        arg2 = c_ushort(buf_no)
        arg3 = c_uint(buf_size)
        ret = self.__SPC_get_stream_buffer_size(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_get_buffer_from_stream(self, stream_hndl, buf_no, buf_size, data_buf, free_buf):

        arg1 = c_short(stream_hndl)
        arg2 = c_ushort(buf_no)
        arg3 = c_uint(buf_size)
        arg4 = data_buf
        arg5 = c_short(free_buf)
        ret = self.__SPC_get_buffer_from_stream(arg1, arg2, arg3, arg4, arg5)
        return ret, arg1, arg2, arg3, arg4, arg5
    
    # Other functions

    def SPC_get_error_string(self, error_id, dest_string, max_length):

        arg1 = c_short(error_id)
        arg2 = dest_string
        arg3 = c_short(max_length)
        ret = self.__SPC_get_error_string(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_get_detector_info(self, previous_type, det_type, fname):

        arg1 = c_short(previous_type)
        arg2 = c_short(det_type)
        arg3 = fname
        ret = self.__SPC_get_detector_info(arg1, arg2, arg3)
        return ret, arg1, arg2, arg3
    
    def SPC_close(self, void):

        ret = self.__SPC_close(void)
        return ret

    def translate_status(self, status):
        
        # Define the status codes
        status_codes = {
            0: 'SPC_OVERFL',
            1: 'SPC_OVERFLOW',
            2: 'SPC_TIME_OVER',
            3: 'SPC_COLTIM_OVER',
            4: 'SPC_CMD_STOP',
            5: 'SPC_REPTIM_OVER',
            6: 'SPC_SEQ_GAP',
            7: 'SPC_ARMED',
            8: 'SPC_COLTIM_2OVER',
            9: 'SPC_REPTIM_2OVER',
            10: 'SPC_FOVFL',
            11: 'SPC_FEMPTY',
            12: 'SPC_WAIT_TRG',
            13: 'SPC_SEQ_GAP150',
            14: 'SPC_SEQ_STOP',
            15: 'SPC_HFILL_NRDY'
        }

        # Convert the byte string to an integer
        status = int.from_bytes(status, byteorder='little')
        binary_str = bin(status)[2:]
        binary_str = binary_str.zfill(16)
        binary_str = binary_str[::-1]
        status_msg = []
        # Check each status code
        for bit_index, code in status_codes.items():
            if binary_str[bit_index] == '1':
                status_msg.append(code)
        return status_msg
    
if __name__ == '__main__':

    import time
    import matplotlib.pyplot as plt

    print(SPCdata)
    print('hola mundo')
    tcspc = SPCDllWrapper()

    ini_file_path = os.path.abspath('C:\Program Files (x86)\BH\SPCM\spcm.ini')
    #ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\new_settings.ini')

    init_status, args = tcspc.SPC_init(ini_file_path)
    print(f'Init status: {init_status} with args: {args}')

    status, mode, force_use, in_use = tcspc.SPC_set_mode(130, 1, 1)
    print(f'Get mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

    module_no = 0
    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

    data.collect_time = 3
    status, mod_no, data = tcspc.SPC_set_parameters(0, data)
    print(f'Set parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

    status, mod_no, adc_resolution, no_of_routing_bits, mem_info = tcspc.SPC_configure_memory(-1, 10, 0, SPCMemConfig())
    print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
    no_of_blocks = mem_info.max_block_no

    page_no = 0

    status, mod_no, page = tcspc.SPC_set_page(-1, page_no)
    print(f'Set page status: {status} with mod_no: {mod_no} and page: {page}')

    status, block, mod_no, page, fill_value = tcspc.SPC_fill_memory(-1, -1, page_no, 1)
    print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')

    status, mod_no = tcspc.SPC_start_measurement(module_no)
    print(f'Start measurement status: {status} with mod_no: {mod_no}')

    state_var = c_short()
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    print(tcspc.translate_status(state))

    red_factor = 1
    no_of_points = int(mem_info.block_length / red_factor)
    print(f'Max block no: {mem_info.max_block_no}')
    print(f'Blocks per frame: {mem_info.blocks_per_frame}')
    print(f'Frames per page: {mem_info.frames_per_page}')
    print(f'Max page: {mem_info.maxpage}')
    print(f'Block length: {mem_info.block_length}')
    print(f'No of points: {no_of_points}')
    data_buffer = (c_ushort * no_of_points)()

    print('Sleeping for a sec')
    time.sleep(3)

    state_var = c_short()
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    print(tcspc.translate_status(state))

    
    status, mod_no, block, page, reduction_factor, var_from, var_to, data = tcspc.SPC_read_data_block(module_no, 0, page_no, red_factor, 0, no_of_points - 1, data_buffer)
    print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
    print(f'Data list: {list(data_buffer)}')

    #plt.plot(data_buffer)
    #plt.show()