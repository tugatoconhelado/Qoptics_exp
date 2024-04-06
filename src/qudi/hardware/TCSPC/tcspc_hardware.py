# -*- coding: utf-8 -*-

__all__ = ['TemplateHardware']

import time

from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.hardware.tcspc.tcspc import SPCDllWrapper
from qudi.core.module import Base
from qudi.hardware.tcspc.spc_def import *
import bh_spc
from bh_spc import spcm
import os
import copy
import ctypes
import numpy as np



class TCSPCHardware(Base):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()
        self.module_no = 0


    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        self.stop_measurement(self.module_no)
        spcm.close()

    def initialise_tcspc(self):
        """
        Initialise the TCSPC hardware
        
        Returns:
        SPCDllWrapper
            The wrapper for the TCSPC hardware
        """
        self.module_no = 0
        ini_file_path = os.path.abspath(r'C:\EXP\python\Qoptics_exp\new_settings.ini')
        spcm.init(ini_file_path)
        spcm.set_mode(spcm.DLLOperationMode.HARDWARE, True, [True])
        print(getattr(spcm.ParID, 'COLLECT_TIME'))

        status = spcm.get_init_status(self.module_no)

        self._tcspc_params = spcm.get_parameters(self.module_no)

        return status

    def set_SPC_param(self, param : str, value):

        setted_param = self._set_SPC_param_to_module(self.module_no)
        return getattr(self._tcspc_params, param)

    def get_SPC_param(self, param: str):

        return self._get_SPC_param_from_module(param)

    def _get_SPC_param_from_module(self, param: str):

        param_id = getattr(spcm.ParID, param)
        value = spcm.get_parameter(self.module_no, param_id)
        return value

    def _set_SPC_param_to_module(self, param: str, value):

        param_id = getattr(spcm.ParID, param)
        spcm.set_parameter(self.module_no, param_id, value)
        setted_parameter = self._get_SPC_param_from_module(param)
        setattr(self._tcspc_params, param, setted_parameter)
        return setted_parameter

    def get_SPC_params_from_module(self, module_no: int = 0):
        """
        Get the parameters of the SPCdata object from the TCSPC hardware
        
        Args:
        module_no: int
            The module number
        
        Returns:
        SPCdata
            The SPCdata object
        """
        params = spcm.get_parameters(module_no)
        self._tcspc_params = params
        return params

    def set_SPC_params_to_module(self, module_no):
        """
        Set the parameters of the SPCdata object to the TCSPC hardware

        Also updates the internal SPCdata object with the parameters from
        the hardware.
        
        Args:
        module_no: int
            The module number
        
        Returns:
        SPCdata
            The SPCdata object
        """
        spcm.set_parameters(module_no, self._tcspc_params)
        params = self._get_SPC_params_from_module(module_no)
        return params
    
    def init_fifo_measurement(self, module_no):

        self.log.info('Initialising FIFO measurement')
        spcm.set_parameter(module_no, spcm.ParID.MODE, 1) # Sets FIFO Mode
        self._tcspc_params.stop_on_time = 1
        self.set_SPC_params_to_module(module_no)

    def start_measurement(self, module_no):

        self.log.info('Starting measurement')
        spcm.start_measurement(module_no)

    def read_rate_counter(self, module_no):

        rates = spcm.read_rates(module_no)
        return rates
    
    def pause_measurement(self, module_no):

        pass
        #status, mod_no = self._tcspc_wrapper.SPC_pause_measurement(module_no)
        #return status

    def restart_measurement(self, module_no):

        pass
        #status, mod_no = self._tcspc_wrapper.SPC_restart_measurement(module_no)
        #return status

    def stop_measurement(self, module_no):

        spcm.stop_measurement(module_no)

    def clear_rates(self, module_no):
            
        spcm.clear_rates(module_no)

    def read_data_from_tcspc(self, module_no, buf_size):

        buf = spcm.read_fifo_to_array(module_no, buf_size)
        #records = np.concatenate(buf).view(np.uint32)
        return buf


    def test_state(self, module_no, print_status=False):

        status = spcm.test_state(module_no)

        return status

