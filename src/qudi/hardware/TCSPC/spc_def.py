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

# masks for SPC module state - function SPC_test_state
SPC_OVERFL = 0x1  # stopped on overflow
SPC_OVERFLOW = 0x2  # overflow occurred
SPC_TIME_OVER = 0x4  # stopped on expiration of collection timer
SPC_COLTIM_OVER = 0x8  # collection timer expired
SPC_CMD_STOP = 0x10  # stopped on user command
SPC_ARMED = 0x80  # measurement in progress (current bank)
SPC_REPTIM_OVER = 0x20  # repeat timer expired
SPC_COLTIM_2OVER = 0x100  # second overflow of collection timer
SPC_REPTIM_2OVER = 0x200  # second overflow of repeat timer

# masks valid only for modules SPC130, SPC6x0
SPC_SEQ_GAP = 0x40  # Sequencer is waiting for other bank to be armed

# masks valid only for modules SPC13x, SPC6x0, SPC830, SPC140, SPC930, SPC15x, SPC16x,18x
# in normal modes when sequencer is enabled
SPC_FOVFL = 0x400  # Fifo overflow,data lost, fifo modes only
SPC_FEMPTY = 0x800  # Fifo empty, fifo modes only

# masks valid only for SPC7x0, SPC830, SPC140, SPC930, SPC15x, SPC131-7, SPC16x,18x modules
SPC_FBRDY = 0x800  # Flow back of scan finished, scan modes only
SPC_SCRDY = 0x400  # Scan ready (data can be read ), scan modes only
SPC_MEASURE = 0x40  # Measurement active = no margin, no wait for trigger, armed
SPC_WAIT_TRG = 0x1000  # wait for trigger
SPC_HFILL_NRDY = 0x8000  # hardware fill not finished

# masks valid only for SPC140, SPC930, SPC15x, SPC131-7, SPC16x,18x modules
SPC_SEQ_STOP = 0x4000  # disarmed (measurement stopped) by sequencer
SPC_SEQ_GAP150 = 0x2000  # SPC15x, SPC16x,18x, SPC131-7 - Sequencer is waiting for other bank to be armed

# normal and Scan In modes when sequencer is enabled
# mask for SPC140, SPC830, SPC15x, SPC16x,18x, DPC230 modules ( in FIFO IMAGE mode )
SPC_WAIT_FR = 0x2000  # FIFO IMAGE measurement waits for the frame signal to stop

# masks valid only for DPC230 modules
SPC_FOVFL2 = 0x800  # TDC 2 Fifo overflow,data lost
SPC_FOVFL1 = 0x400  # TDC 1 Fifo overflow,data lost
SPC_FEMPTY2 = 0x200  # TDC 2 Fifo empty
SPC_FEMPTY1 = 0x100  # TDC 1 Fifo empty
SPC_ARMED1 = 0x80  # TDC 1 armed
SPC_ARMED2 = 0x4000  # TDC 2 armed
SPC_CTIM_OVER2 = 0x20  # collection timer of TDC 2 expired
SPC_CTIM_OVER1 = 0x8  # collection timer of TDC 1 expired

# other flags valid for DPC230 and defined above :
# SPC_MEASURE, SPC_TIME_OVER, SPC_WAIT_TRG , SPC_WAIT_FR,
# sequencer state bits - returned from function SPC_get_sequencer_state
SPC_SEQ_ENABLE = 0x1  # sequencer is enabled
SPC_SEQ_RUNNING = 0x2  # sequencer is running
SPC_SEQ_GAP_BANK = 0x4  # sequencer is waiting for other bank to be armed

# SPC_PARAMETERS_KEYWORDS
CFD_LIMIT_LOW = 0
CFD_LIMIT_HIGH = 1
CFD_ZC_LEVEL = 2
CFD_HOLDOFF = 3
SYNC_ZC_LEVEL = 4
SYNC_FREQ_DIV = 5
SYNC_HOLDOFF = 6
SYNC_THRESHOLD = 7
TAC_RANGE = 8
TAC_GAIN = 9
TAC_OFFSET = 10
TAC_LIMIT_LOW = 11
TAC_LIMIT_HIGH = 12
ADC_RESOLUTION = 13
EXT_LATCH_DELAY = 14
COLLECT_TIME = 15
DISPLAY_TIME = 16
REPEAT_TIME = 17
STOP_ON_TIME = 18
STOP_ON_OVFL = 19
DITHER_RANGE = 20
COUNT_INCR = 21
MEM_BANK = 22
DEAD_TIME_COMP = 23
SCAN_CONTROL = 24
ROUTING_MODE = 25
TAC_ENABLE_HOLD = 26
MODE = 27
SCAN_SIZE_X = 28
SCAN_SIZE_Y = 29
SCAN_ROUT_X = 30
SCAN_ROUT_Y = 31
SCAN_POLARITY = 32
SCAN_FLYBACK = 33
SCAN_BORDERS = 34
PIXEL_TIME = 35
PIXEL_CLOCK = 36
LINE_COMPRESSION = 37
TRIGGER = 38
EXT_PIXCLK_DIV = 39
RATE_COUNT_TIME = 40
MACRO_TIME_CLK = 41
ADD_SELECT = 42
ADC_ZOOM = 43
XY_GAIN = 44
IMG_SIZE_X = 45
IMG_SIZE_Y = 46
IMG_ROUT_X = 47
IMG_ROUT_Y = 48
MASTER_CLOCK = 49
ADC_SAMPLE_DELAY = 50
DETECTOR_TYPE = 51
TDC_CONTROL = 52
CHAN_ENABLE = 53
CHAN_SLOPE = 54
CHAN_SPEC_NO = 55
TDC_OFFSET1 = 56
TDC_OFFSET2 = 57
TDC_OFFSET3 = 58
TDC_OFFSET4 = 59

# enum spc_parameters_enum
SPC_PARAMETERS_KEYWORDS = list(range(60))

