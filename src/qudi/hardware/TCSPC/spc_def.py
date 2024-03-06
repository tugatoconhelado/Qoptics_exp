from ctypes import (
    c_short, c_ushort, c_float, c_ulong, c_char,
    c_int, c_uint, c_uint64, c_double, Structure,
    c_long
)

class SPCdata(Structure):
    _fields_ = [
        ('base_adr', c_ushort),
        ('init', c_short),
        ('cfd_limit_low', c_float),
        ('cfd_limit_high', c_float),
        ('cfd_zc_level', c_float),
        ('cfd_holdoff', c_float),
        ('sync_zc_level', c_float),
        ('sync_holdoff', c_float),
        ('sync_threshold', c_float),
        ('tac_range', c_float),
        ('sync_freq_div', c_short),
        ('tac_gain', c_short),
        ('tac_offset', c_float),
        ('tac_limit_low', c_float),
        ('tac_limit_high', c_float),
        ('adc_resolution', c_short),
        ('ext_latch_delay', c_short),
        ('collect_time', c_float),
        ('display_time', c_float),
        ('repeat_time', c_float),
        ('stop_on_time', c_short),
        ('stop_on_ovfl', c_short),
        ('dither_range', c_short),
        ('count_incr', c_short),
        ('mem_bank', c_short),
        ('dead_time_comp', c_short),
        ('scan_control', c_ushort),
        ('routing_mode', c_ushort),
        ('tac_enable_hold', c_float),
        ('pci_card_no', c_short),
        ('mode', c_ushort),
        ('scan_size_x', c_ulong),
        ('scan_size_y', c_ulong),
        ('scan_rout_x', c_ulong),
        ('scan_rout_y', c_ulong),
        ('scan_flyback', c_ulong),
        ('scan_borders', c_ulong),
        ('scan_polarity', c_ushort),
        ('pixel_clock', c_ushort),
        ('line_compression', c_ushort),
        ('trigger', c_ushort),
        ('pixel_time', c_float),
        ('ext_pixclk_div', c_ulong),
        ('rate_count_time', c_float),
        ('macro_time_clk', c_short),
        ('add_select', c_short),
        ('text_eep', c_short),
        ('adc_zoom', c_short),
        ('img_size_x', c_ulong),
        ('img_size_y', c_ulong),
        ('img_rout_x', c_ulong),
        ('img_rout_y', c_ulong),
        ('xy_gain', c_short),
        ('master_clock', c_short),
        ('adc_sample_delay', c_short),
        ('detector_type', c_short),
        ('chan_enable', c_ulong),
        ('chan_slope', c_ulong),
        ('chan_spec_no', c_ulong),
        ('tdc_control', c_ulong),
        ('tdc_offset', c_float),
    ]

class SPC_Adjust_Para(Structure):
    _fields_ = [
        ('vrt1', c_short),
        ('vrt2', c_short),
        ('vrt3', c_short),
        ('dith_g', c_short),
        ('gain_1', c_float),
        ('gain_2', c_float),
        ('gain_4', c_float),
        ('gain_8', c_float),
        ('tac_r0', c_float),
        ('tac_r1', c_float),
        ('tac_r2', c_float),
        ('tac_r4', c_float),
        ('tac_r8', c_float),
        ('sync_div', c_short),
    ]

class SPCModInfo(Structure):
    _fields_ = [
        ('module_type', c_short),
        ('bus_number', c_short),
        ('slot_number', c_short),
        ('in_use', c_short),
        ('init', c_short),
        ('base_adr', c_ushort)
    ]

class SPC_EEP_Data(Structure):
    _fields_ = [
        ('module_type', c_char),
        ('serial_no', c_char),
        ('date', c_char),
        ('adj_para', SPC_Adjust_Para),
    ]

class rate_values(Structure):
    _fields_ = [
        ('sync_rate', c_float),
        ('cfd_rate', c_float),
        ('tac_rate', c_float),
        ('adc_rate', c_float),
    ]

class SPCMemConfig(Structure):
    _fields_ = [
        ('max_block_no', c_long),
        ('blocks_per_frame', c_long),
        ('frames_per_page', c_long),
        ('maxpage', c_long),
        ('block_length', c_short),
    ]

class PhotStreamInfo(Structure):
    _fields_ = [
        ('fifo_type', c_short),
        ('stream_type', c_short),
        ('mt_clock', c_int),
        ('rout_chan', c_short),
        ('what_to_read', c_short),
        ('no_of_files', c_short),
        ('no_of_ready_files', c_short),
        ('base_name', c_char),
        ('cur_name', c_char),
        ('first_no', c_short),
        ('cur_no', c_short),
        ('fifo_overruns', c_int),
        ('stream_size', c_uint64),
        ('cur_stream_offs', c_uint64),
        ('cur_file_offs', c_uint64),
        ('invalid_phot', c_uint64),
        ('read_photons', c_uint64),
        ('read_0_mark', c_uint64),
        ('read_1_mark', c_uint64),
        ('read_2_mark', c_uint64),
        ('read_3_mark', c_uint64),
        ('start01_offs', c_uint),
        ('no_of_buf', c_short),
        ('no_of_ready_buf', c_short),
        ('cur_buf_offs', c_uint),
        ('start_OR_mask', c_uint),
        ('start_AND_mask', c_uint),
        ('stop_OR_mask', c_uint),
        ('stop_AND_mask', c_uint),
        ('start_found', c_short),
        ('stop_reached', c_short),
        ('start_time', c_double),
        ('stop_time', c_double),
        ('curr_time', c_double),
        ('start_found_chan', c_uint),
        ('stop_found_chan', c_uint)
    ]

class PhotInfo(Structure):
    _fields_ = [
        ('mtime_lo', c_ulong),
        ('mtime_hi', c_ulong),
        ('micro_time', c_ushort),
        ('rout_chan', c_ushort),
        ('flags', c_ushort),
    ]

class PhotInfo64(Structure):
    _fields_ = [
        ('mtime', c_uint64),
        ('micro_time', c_ushort),
        ('rout_chan', c_ushort),
        ('flags', c_ushort),
    ]