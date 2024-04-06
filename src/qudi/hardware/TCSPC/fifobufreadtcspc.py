from ctypes import (
    CDLL, POINTER, c_char_p, c_bool, c_double, c_int,
    c_short, c_void_p, c_float, c_ushort, Structure,
    c_ulong, c_long, c_uint, c_uint64, byref, sizeof, cdll, pointer
)
from qudi.hardware.tcspc.spc_def import *
import struct
import time
from qudi.hardware.tcspc.tcspc import SPCDllWrapper
import os
import matplotlib.pyplot as plt
import copy
import numpy as np
import matplotlib.pyplot as plt

def initialise_tcspc(tcspc, module_no, file=None):

    ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\new_settings.ini')
    init_status, args = tcspc.SPC_init(ini_file_path)
    print(f'Init status: {init_status} with args: {args}')

    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status, mode, force_use, in_use = tcspc.SPC_set_mode(0, 1, 1)
    print(f'Set mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

    init_status, args = tcspc.SPC_get_init_status(module_no)
    print(f'Init status of module {module_no}: {init_status} with args: {args}')

    status = tcspc.SPC_get_mode()
    print(f'Get mode status: {status}')

    status, mod_no, data = tcspc.SPC_get_parameters(module_no)
    print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

    return data

def test_state(tcspc, module_no, print_status=False):

    state_var = 0
    status, mod_no, state = tcspc.SPC_test_state(module_no, state_var)
    #print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
    status_code = tcspc.translate_status(state)
    if print_status:
        print(f'Status code: {status_code}')

    return status_code

def empty_memory_bank(tcspc, module_no, block, page, fill_value):

    status, mod_no, block, page, fill_value = tcspc.SPC_fill_memory(module_no, block, page, fill_value)
    print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')
    continue_fill = True
    while continue_fill:
        status_code = test_state(tcspc, module_no)

        if 'SPC_HFILL_NRDY' in status_code:
            print('Memory bank not filled')
            time.sleep(1)
        else:
            continue_fill = False
            print('Memory bank filled')
    
def configure_memory(tcspc, adc_resolution, no_of_routing_bits, module_no, page_no=1):

    status, mod_no, adc_resolution, no_of_routing_bits, mem_info = tcspc.SPC_configure_memory(module_no, adc_resolution, no_of_routing_bits, SPCMemConfig())
    print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')

    return mem_info

def init_fifo_measurement(tcspc, module_no):

    fifo_stopt_possible = True
    first_write = 1
    current_mode = 0

    # Disables the sequencer
    status, mod_no, enable = tcspc.SPC_enable_sequencer(module_no, 0)
    print(f'Enable sequencer status: {status} with mod_no: {mod_no} and enable: {enable}')

    #status, mod_no, par_id, value = tcspc.SPC_get_parameter(module_no, 27, current_mode)
    #print(f'Get parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    #print(current_mode)

    # Sets MODE to 2 (FIFO mode)
    status, mod_no, par_id, value = tcspc.SPC_set_parameter(module_no, 27, 1)
    print(f'Set parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    status, mod_no, par_id, current_mode = tcspc.SPC_get_parameter(module_no, 27, current_mode)
    print(f'Get parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {current_mode}')

    print(f'Current mode: {current_mode}')

    scan_polarity = 0
    rout_mode = 0

    # Get SCAN_POLARITY (not used in this case, only for scanning)
    status, mod_no, par_id, scan_polarity = tcspc.SPC_get_parameter(module_no, 32, scan_polarity)
    print(f'Get parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {scan_polarity}')

    print(f'Scan polarity: {scan_polarity}')

    # Get ROUT_MODE (not used)
    status, mod_no, par_id, rout_mode = tcspc.SPC_get_parameter(module_no, 25, rout_mode)
    print(f'Get parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {rout_mode}')

    print(f'Routing mode: {rout_mode}')

    # Sets STOP_ON_TIME to 0
    status, mod_no, par_id, value = tcspc.SPC_set_parameter(module_no, 18, 0)
    print(f'Set parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    # Sets STOP_ON_OVFL to 0
    status, mod_no, par_id, value = tcspc.SPC_set_parameter(module_no, 19, 0)
    print(f'Set parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    # Sets STOP_ON_OVFL to 0
    status, mod_no, par_id, value = tcspc.SPC_set_parameter(module_no, 15, 1)
    print(f'Set parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    if fifo_stopt_possible:
        # If FIFO stop after coltime is possible 
        # Set STOP_ON_TIME to 1
        status, mod_no, par_id, value = tcspc.SPC_set_parameter(module_no, 18, 1)
        print(f'Set parameter status: {status} with mod_no: {mod_no}, par_id: {par_id} and value: {value}')

    max_words_in_buffer = 2 * 200000

    return max_words_in_buffer

def save_photons_in_file(filepath, words_in_buf, data_buffer):

    first_frame = (c_ushort * 3)()
    fifo_type = 1
    stream_type = 0
    mt_clock = 0
    spc_header = 0
    module_no = 0
    ret, mod_no, rfifo_type, rstream_type, rmt_clock, rspc_header = tcspc.SPC_get_fifo_init_vars(module_no, fifo_type, stream_type, mt_clock, spc_header)
    print(f'Get fifo init vars status: {ret} with mod_no: {mod_no}, fifo_type: {rfifo_type}, stream_type: {rstream_type}, mt_clock: {rmt_clock} and spc_header: {rspc_header}')
    print(spc_header)
    print(rspc_header)
    first_frame[0] = rspc_header.value & 0xFFFF
    first_frame[1] = (rspc_header.value >> 16) & 0xFFFF
    first_frame[2] = 0

    with open(filepath, "wb") as stream:
        stream.write(struct.pack('H' * 2, *first_frame[:2])) # write 2 words (32 bits)

    # Write photons buffer to the file
    with open(filepath, "ab") as stream:
        ret = stream.write(bytes(data_buffer[:2 * words_in_buf]))

    if ret != 2 * words_in_buf:
        # Error occurred, return -1
        return -1

    # No errors occurred, return 0
    return 0

def create_histogram(data, t_values):
    crhistogram = []
    for t in t_values:
        count = sum(1 for d in data if d == t)
        crhistogram.append(count)
    return crhistogram, t_values


if __name__ == '__main__':

    module_no = 0

    tcspc = SPCDllWrapper()
    data = initialise_tcspc(tcspc, module_no, file=r'C:\EXP\python\Qoptics_exp\spcm_fifo_test.ini')
    print(data.mode)

    max_words_in_buffer = init_fifo_measurement(tcspc, module_no)
    fifo_stopt_possible = True
    buffer = (c_ushort * max_words_in_buffer)()

    tcspc.SPC_set_parameter(module_no, STOP_ON_TIME, 1)

    col_time = 3.0
    tcspc.SPC_set_parameter(module_no, COLLECT_TIME, col_time)

    photons_to_read = 15000000
    words_per_photon = 2

    photon_left = photons_to_read
    phot_in_buf = 0

    # allocate buffer for photons extracted from buffered stream
    phot_buffer = (PhotInfo64 * photons_to_read)()
    phot_buf_size = sizeof(phot_buffer)
    what_to_read = 1 # valid photons    

    ret, mod_no, fifo_type, stream_type, mt_clock, spc_header = tcspc.SPC_get_fifo_init_vars(module_no, 1, 0, 0, 0)
    print(f'Get fifo init vars status: {ret} with mod_no: {mod_no}, fifo_type: {fifo_type}, stream_type: {stream_type}, mt_clock: {mt_clock}')
    print(bytes(stream_type))

    stream_hndl, fifo_type, stream_type, what_to_read, mt_clock, start01_offs = tcspc.SPC_init_buf_stream(
        fifo_type.value, stream_type.value, what_to_read, mt_clock.value, 0)
    print(f'Init buf stream status: {stream_hndl} with fifo_type: {fifo_type}, stream_type: {stream_type}, what_to_read: {what_to_read}, mt_clock: {mt_clock}, start01_offs: {start01_offs}')

    status, mod_no = tcspc.SPC_start_measurement(module_no)
    print(f'Start measurement status: {status} with mod_no: {mod_no}')

    continue_acquisition = True
    total_photons_read = 0
    while continue_acquisition:
        status_code = test_state(tcspc, module_no, print_status=False)

        current_cnt = photon_left * words_per_photon
        phot_cnt = photon_left
        phot_ptr = pointer(phot_buffer[phot_in_buf])

        if 'SPC_ARMED' in status_code:
            
            if 'SPC_FEMPTY' in status_code:
                print('FIFO empty')
                continue

            # FIFO contents is read to stream buffers ( on a DLL level) - no need to allocate any external buffer now
            # before the call current_cnt contains required number of words to read from fifo
            status, rstream_hndl, mod_no, current_cnt = tcspc.SPC_read_fifo_to_stream(stream_hndl, module_no, current_cnt)
            #print(f'Read fifo to stream status: {status} with stream_hndl: {stream_hndl} and readed: {current_cnt}')

            # after the call current_cnt contains number of words read from fifo and putted to stream buffers

            # photons can be extracted from the stream directly after reading from FIFO, or in any other moment,
            # also by using other program's thread

            # if you call SPC_get_photons_from_stream in this loop, be aware of the photons rate ( rates.adc_rate)
            # with high photons rates it can cause fifo overrun
            # you can delay or interrupt extracting photons by changing start or stop condition
            # by calling SPC_stream_start(stop)_condition

            # before the call phot_cnt contains required number of photons to get from buffered stream
            ret, rstream_hndl, rphot_ptr, phot_cnt = tcspc.SPC_get_photons_from_stream(stream_hndl, phot_ptr, phot_cnt)
            #print(f'Get photons from stream status: {ret} with stream_hndl: {stream_hndl} and phot_cnt: {phot_cnt}')

            photon_left -= phot_cnt.value
            phot_in_buf += phot_cnt.value

            total_photons_read += current_cnt.value / words_per_photon

        if 'SPC_FOVFL' in status_code:
            print('FIFO overrun')
            continue_acquisition = False

        if 'SPC_TIME_OVER' in status_code:
            print('Time over')
            continue_acquisition = False
            current_cnt = photon_left * words_per_photon
            print('Reading what is left')
            print('Photons left: ', photon_left)
            recovered_photons = 0
            while current_cnt > 0:
                current_cnt = photon_left * words_per_photon # In order to read all that is left
                status, rstream_hndl, mod_no, current_cnt = tcspc.SPC_read_fifo_to_stream(stream_hndl, module_no, current_cnt)
                print(f'Read fifo to stream status: {status} with stream_hndl: {stream_hndl} and readed: {current_cnt}')
                total_photons_read += current_cnt.value / words_per_photon
                current_cnt = current_cnt.value # Check that we readed something for the loop
                recovered_photons += current_cnt / words_per_photon

    print('Escaped loop')

    print(photons_to_read - photon_left)

    ret, mod_no = tcspc.SPC_stop_measurement(module_no)
    print(f'Stop measurement status: {ret} with mod_no: {mod_no}')

    ret, rstream_hndl, stream_info = tcspc.SPC_get_phot_stream_info(stream_hndl)
    print(f'Get phot stream info status: {ret} with stream_hndl: {stream_hndl} and stream_info: {stream_info}')

    print('Total photons read: ', total_photons_read)
    print('Recoverd photons: ', recovered_photons)

    #while recovered_photons > 0:

    phot_cnt = photon_left
    print(f'phot_cnt {phot_cnt}')
    photon_ptr = pointer(phot_buffer[phot_in_buf])
    ret, rstream_hndl, rphot_ptr, phot_cnt = tcspc.SPC_get_photons_from_stream(stream_hndl, photon_ptr, phot_cnt)
    print(f'Get photons from stream status: {ret} with stream_hndl: {stream_hndl} and photon_ptr {photon_ptr} and phot_cnt: {phot_cnt}')
    print(f'Photon pointer {rphot_ptr}')
    print(f'Photon buffer {phot_buffer[10]}')

    total_phot = phot_cnt.value
    micro_times = []
    converted_times = []
    macro_times = []
    flags = []
    for i in range(int(total_photons_read)):
        macro_time = phot_buffer[i].mtime
        #macro_times.append(macro_time)
        micro_time = phot_buffer[i].micro_time #& 0xFFF
        adc_value = 4095 - micro_time & 0xFFF
        flag = phot_buffer[i].flags
        rout_chan = phot_buffer[i].rout_chan
        flagstr = format(flag, '016b')
        flagstr = ' '.join(flagstr[i:i + 4] for i in range(0, len(flagstr), 4))
        #if flag != 0:
            #print(flag)
            #print(f'Photon {i}: Micro time {phot_ptr[i].micro_time} Flags {flagstr} Routing channel {phot_ptr[i].rout_chan}')
        #    if flag & NOT_PHOTON:
        #        print('Not a photon')
        if not (flag & NOT_PHOTON):
            if (micro_time != 0):
                #if rout_chan != 0:
                micro_times.append(micro_time)
                converted_times.append(adc_value)
                flags.append(flag)
                macro_times.append(macro_time)
    print(f'Micro time: {rphot_ptr.contents.micro_time}')
    photon_left -= phot_cnt.value
    phot_in_buf += phot_cnt.value
    recovered_photons -= phot_cnt.value

    print(len(micro_times))
    micro_times = np.array(micro_times)
    macro_times = np.array(macro_times) #* 2e-7
    #print(macro_times)
    #print(micro_times)
    #micro_times = micro_times[micro_times < 5000]
    #micro_times = micro_times[micro_times > 0.001]
    #print(micro_times)
    #print(max(macro_times))
    print(data.tac_range)
    print(data.tac_offset)
    print(data.tac_limit_high)                                                                      
    print(data.tac_limit_low)
    print(data.adc_resolution)
    #print(np.array(flags))

    time_bins = np.arange(4096) #* data.tac_range / 4096
    print(time_bins)
    #histogram, bin_edges = np.histogram(converted_times, bins=4096)
    #bin_edges = bin_edges #* data.tac_range / 4096
    #print(bin_edges)
    #bin_edges = bin_edges[:-1]
    #print(histogram)
    print(len(converted_times))
    print(max(converted_times))
    print(min(converted_times))
    #print(converted_times)
    histogram, bin_edges = create_histogram(converted_times, time_bins)
    #plt.plot(bin_edges * data.tac_range / 4096, histogram)
    #plt.show()
    micro_times = micro_times[micro_times < 4096]
    plt.hist(micro_times, bins=2000, histtype='step')
    plt.show()

    print(spc_header)
    print(type(spc_header.value))
    #print('Saving photons in .ph file')
    #with open('bufferedstreamfifo.ph', 'wb') as file:
    #    lval = spc_header.value & 0x7bffffff
    #    file.write(struct.pack('L', lval))
    #    for phot in phot_buffer:
    #        file.write(phot)

    """
    strbuf_size = 0
    buf_size = 0

    ret, rstream_hndl, stream_info = tcspc.SPC_get_phot_stream_info(stream_hndl)
    print(f'Get phot stream info status: {ret} with stream_hndl: {stream_hndl} and stream_info: {stream_info}')
    print(stream_info.stream_type)
    print(stream_info.no_of_buf)
    if (stream_info.stream_type & FREE_BUF_STREAM) == 0:
        print('Saving spc file')
        # only when buffers were not freed after extracting photons
        #for i in range(0, stream_info.no_of_buf):
        i = 0
        print(f'Buffer {i}')
        # Gets the buffer size
        ret, rstream_hndl, buf_no, rstrbuf_size = tcspc.SPC_get_stream_buffer_size(stream_hndl, i, strbuf_size)
        print(f'Get stream buffer size status: {ret} with buf_no: {buf_no} and strbuf_size: {rstrbuf_size}')

        #if strbuf_size.value != 0:
        #    continue
        #if strbuf_size> buf_size:
        buffer = (c_char_p * strbuf_size)()
        buf_size = strbuf_size

        ret, rstream_hndl, rbuf_no, rbuf_size, rdata_buf, rfree_buf= tcspc.SPC_get_buffer_from_stream(
            stream_hndl, i, strbuf_size, buffer, 0)
        print(f'Get buffer from stream status: {ret} with buf_no: {rbuf_no} and buf_size: {rbuf_size} and data_buf: {rdata_buf} and free_buf: {rfree_buf}')
        words_in_buf = strbuf_size // 2
        save_photons_in_file('bufferedstreamfifotest.spc', words_in_buf, buffer)
    """
    status, rstream_hndl = tcspc.SPC_close_phot_stream(stream_hndl)
    print(f'Close phot stream status: {status} with stream_hndl: {rstream_hndl}')
    