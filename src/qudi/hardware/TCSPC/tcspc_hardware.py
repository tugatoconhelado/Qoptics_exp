# -*- coding: utf-8 -*-

__all__ = ['TemplateHardware']

import time

from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.hardware.tcspc.tcspc import SPCDllWrapper
from qudi.core.module import Base
from qudi.hardware.tcspc.spc_def import (
    SPCdata, SPCModInfo, SPC_EEP_Data, SPC_Adjust_Para,
    SPCMemConfig, PhotStreamInfo, PhotInfo, PhotInfo64,
    rate_values
)
import os
import copy
import ctypes


class TCSPCHardware(Base):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()
        self._tcspc_wrapper = SPCDllWrapper()
        self._tcspc_params = SPCdata()

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def set_SPC_params(self, param: str, value: float):
        """
        Set the parameters of the SPCdata object
        
        Args:
        params: str
            The parameter to be set
        value: float
            The value to be set
        
        Returns:
        float
            The value of the parameter after setting
        """
        setattr(self._tcspc_params, param, value)
        return getattr(self._tcspc_params, param)
    
    def get_SPC_params(self, params: dict, module_no: int = 0):

        self._tcspc_params = self.get_SPC_params_from_module(module_no)
        for param, value in params.items():
            if param != 'mode':
                params[param] = getattr(self._tcspc_params, param)
        return params

    def get_SPC_params_from_module(self, module_no: int = 0):

        params_data = SPCdata()
        status, mod_no, params = self._tcspc_wrapper.SPC_get_parameters(module_no, params_data)
        return params

    def set_SPC_params_to_module(self, module_no):
        """
        Set the parameters of the SPCdata object to the TCSPC hardware
        
        Args:
        module_no: int
            The module number
        
        Returns:
        SPCdata
            The SPCdata object
        """
        status, mod_no, data = self._tcspc_wrapper.SPC_set_parameters(module_no, self._tcspc_params)
        #print(f'Set parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')
        return data
    
    def initialise_tcspc(self):
        """
        Initialise the TCSPC hardware
        
        Returns:
        SPCDllWrapper
            The wrapper for the TCSPC hardware
        """
        ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\spcm_test.ini')
        init_status, args = self._tcspc_wrapper.SPC_init(ini_file_path)
        print(f'Init status: {init_status} with args: {args}')
        
        status, mode, force_use, in_use = self._tcspc_wrapper.SPC_set_mode(0, 1, 2)
        print(f'Get mode status: {status} with mode: {mode} and force_use: {force_use} and in_use: {in_use}')

        self.module_no = 0
        init_status, args = self._tcspc_wrapper.SPC_get_init_status(self.module_no)
        print(f'Init status of module {self.module_no}: {init_status} with args: {args}')

        status, mod_no, data = self._tcspc_wrapper.SPC_get_parameters(self.module_no)
        print(f'Get parameters status: {status} with mod_no: {mod_no} and data collect time: {data.collect_time}')

        return self._tcspc_wrapper
    
    def configure_memory(self, module_no, page_no=0):
        """
        Configure the memory of the TCSPC hardware
        
        Args:
        module_no: int
            The module number
        page_no: int
            The page number
        
        Returns:
        SPCMemConfig
            The memory configuration
        """

        status, mod_no, adc_resolution, no_of_routing_bits, mem_info = self._tcspc_wrapper.SPC_configure_memory(module_no, 10, 0, SPCMemConfig())
        print(f'Configure memory status: {status} with adc_resolution: {adc_resolution}, no_of_routing_bits: {no_of_routing_bits} and mem_info: {mem_info}')
        self._mem_info = mem_info

        return self._mem_info
    
    def empty_memory_bank(self, module_no, page_no):

        status, mod_no, block, page, fill_value = self._tcspc_wrapper.SPC_fill_memory(module_no, 0, page_no, 1)
        print(f'Fill memory status: {status} with block: {block}, page: {page} and fill_value: {fill_value}')
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
        status, mod_no, state = self._tcspc_wrapper.SPC_test_state(module_no, state_var)
        #print(f'Test state status: {status} with mod_no: {mod_no} and state: {bytes(state)}')
        status_code = self._tcspc_wrapper.translate_status(state)
        if print_status:
            print(f'Status code: {status_code}')

        return status_code
    
    def start_single_mode_measurement(self, module_no, page_no):
        """
        Start a single mode measurement.

        In order to do this the page to store the data must be set,
        the sequencer must be disabled and the memory bank must be emptied.
        
        Args:
        module_no: int
            The module number
        page_no: int
            The page number

        Returns:
        None
        """
        status, mod_no, page = self._tcspc_wrapper.SPC_set_page(module_no, page_no)
        print(f'Set page status: {status} with mod_no: {mod_no} and page: {page}')

        status, mod_no, enable = self._tcspc_wrapper.SPC_enable_sequencer(module_no, 0)
        print(f'Enable sequencer status: {status} with mod_no: {mod_no} and enable: {enable}')

        self.empty_memory_bank(module_no, page_no)

        status, mod_no = self._tcspc_wrapper.SPC_start_measurement(module_no)
        print(f'Start measurement status: {status} with mod_no: {mod_no}')

    def read_rate_counter(self, module_no):

        rate_storage = rate_values()
        status, mod_no, rate = self._tcspc_wrapper.SPC_read_rates(module_no, rate_storage)
        #print(f'Read rate status: {status} with mod_no: {mod_no} and rate: {rate}')
        return rate
    
    def clear_rates(self, module_no):
            
        status, mod_no = self._tcspc_wrapper.SPC_clear_rates(module_no)
        #print(f'Clear rates status: {status} with mod_no: {mod_no}')

    def read_data_from_tcspc(self, module_no, red_factor=1):

        no_of_points = int(self._mem_info.block_length / red_factor)
        data_buffer = data_buffer = (ctypes.c_ushort * no_of_points)()
        status, mod_no, block, page, reduction_factor, var_from, var_to, data = self._tcspc_wrapper.SPC_read_data_block(
            module_no, 0, 0, red_factor, 0, no_of_points - 1, data_buffer)
        print(f'Read data block status: {status} with mod_no: {mod_no}, block: {block}, page: {page}, reduction_factor: {reduction_factor}, var_from: {var_from}, var_to: {var_to} and data: {data}')
        readed_data = list(copy.copy(data))
        print(readed_data)
        return readed_data