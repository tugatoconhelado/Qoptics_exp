
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import QObject, Signal
import pyvisa as visa
from pyvisa.constants import StopBits, Parity
import logging
from time import sleep
import serial



class IonGunHardware(Base):
    """
    Models the turbo pump instrument
    
    Properties
    ----------
    
    Methods
    -------
    connect
    
    _pad_payload
    
    _format_id
    
    _calculate_checksum
    """
    
    status_msg_signal = Signal(str)

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        self.communication = {'BAUDRATE' : 1200,
                              'DATA_BITS' : 8,
                              'PARITY' : Parity.none,
                              'START_BITS' : 1,
                              'STOP_BITS' : StopBits.one}
        self.rm = visa.ResourceManager('@py')
        self.devices = self.rm.list_resources()
        self.connected = False
        self.data_types = {0:{'description':'False / true', 'length':'06', 'example':'000000 / 111111'},
            1:{'description':'Positive integer number', 'length':'06', 'example':'000000 to 999999'},
            2:{'description':'Positive fixed comma number', 'length':'06', 'example':'001571' 'equal to 15,71'},
            4:{'description':'Symbol chain', 'length':'06', 'example':'TC_400'},
            7:{'description':'Positive integer number', 'length':'03', 'example':'000 to 999'},
            11:{'description':'Symbol chain', 'length':'16', 'example':'BrezelBier&Wurst'}}
        self.commands = {'Remote enable':{'ASCII string':'RE', 'description':'Remote enable','access':'NP'},
                'Local':{'ASCII string':'LO', 'description':'Local','access':'NP'},
                'Enable local':{'ASCII string':'EN', 'description':'Enable local','access':'NP'},
                'Operate':{'ASCII string':'OP', 'description':'Operate','access':'NP'},
                'Standby':{'ASCII string':'SB', 'description':'Standby','access':'NP'},
                'Degas':{'ASCII string':'DG', 'description':'Degas','access':'NP'},
                'Off':{'ASCII string':'OF', 'description':'Off','access':'NP'},
                'Reset powe unit':{'ASCII string':'RSE', 'description':'Reset power unit','access':'NP'},
                'HV on':{'ASCII string':'HE', 'description':'High Voltage on','access':'NP'},
                'HV off':{'ASCII string':'HA', 'description':'High Voltage off','access':'NP'},
                'Operating status':{'ASCII string':'OS', 'description':'Operating status','access':'NP'},
                'Error status':{'ASCII string':'ES', 'description':'Error status','access':'R'},
                'Emision current':{'ASCII string':'EC', 'description':'Emision current','access':'RW', 'min':10, 'max':10000, 'scale factor':0.1, 'unit':'µA'},
                'Energy':{'ASCII string':'EN', 'description':'Energy','access':'RW', 'min':0, 'max':5000, 'scale factor':1, 'unit':'eV'},
                'Extractor voltage':{'ASCII string':'EX', 'description':'Extractor voltage','access':'RW', 'min':60, 'max':100, 'scale factor':100, 'unit':'%'},
                'Focus 1 voltage':{'ASCII string':'F1', 'description':'Focus 1 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit':'%'},
                'Focus 2 voltage':{'ASCII string':'F2', 'description':'Focus 2 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit':'%'},
                'Position X':{'ASCII string':'X0', 'description':'Position X','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit':'µA'},
                'Position Y':{'ASCII string':'Y0', 'description':'Position Y','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit':'µA'},
                'Width X':{'ASCII string':'WX', 'description':'Width X','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit':'µA'},
                'Width Y':{'ASCII string':'WY', 'description':'Width Y','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit':'µA'},
                'Blanking X':{'ASCII string':'BX', 'description':'Blanking X','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit':'%'},
                'Blanking Y':{'ASCII string':'BY', 'description':'Blanking Y','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit':'%'},
                'Blanking level':{'ASCII string':'BL', 'description':'Blanking level','access':'RW', 'min':0, 'max':1, 'scale factor':1, 'unit':''},
                'Time per dot':{'ASCII string':'TD', 'description':'Time per dot','access':'RW', 'min':30, 'max':30000, 'scale factor':1, 'unit':'µs'},
                'Angle phi':{'ASCII string':'PH', 'description':'Angle phi','access':'RW', 'min':-90, 'max':90, 'scale factor':1, 'unit':'°'},
                'Angle theta':{'ASCII string':'TH', 'description':'Angle theta','access':'RW', 'min':-85, 'max':85, 'scale factor':1, 'unit':'°'},
                'L': {'ASCII string':'L', 'description':'lenght L','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit':'µm'},
                'D': {'ASCII string':'D', 'description':'diameter D','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit':'µm'},
                'Deflection X':{'ASCII string':'VX', 'description':'Deflection X','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit':'V/°'},
                'Deflection Y':{'ASCII string':'VY', 'description':'Deflection Y','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit':'V/°'},
                'Energy current':{'ASCII string':'ENI', 'description':'Energy current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Energy module temperature':{'ASCII string':'ENT', 'description':'Energy module temperature','access':'R', 'scale factor':1, 'unit':'°C'},
                'Extractor current':{'ASCII string':'exi', 'description':'Extractor current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus 1 current':{'ASCII string':'f1i', 'description':'Focus 1 current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus 2 current':{'ASCII string':'f2i', 'description':'Focus 2 current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus module temperature':{'ASCII string':'f1t', 'description':'Focus 1 module temperature','access':'R', 'scale factor':1, 'unit':'°C'},
                'Filament voltage':{'ASCII string':'FU', 'description':'Filament voltage','access':'R', 'scale factor':1, 'unit':'V'},
                'Filament current':{'ASCII string':'FI', 'description':'Filament current','access':'R', 'scale factor':10, 'unit':'A'},
        }
        self.error_comands = {'Current limit error':{'ASCII string':'CL', 'description':'Current limit error','access':'R'},
                'Cathode fail error':{'ASCII string':'VL', 'description':'Cathode fail error','access':'R'},
                'Regulation error':{'ASCII string':'RE', 'description':'Regulation error','access':'R'},
                'Energy error':{'ASCII string':'EN', 'description':'Energy error','access':'R'},
                'Extractor error':{'ASCII string':'EX', 'description':'Extractor error','access':'R'},
                'Focus 1 error':{'ASCII string':'F1', 'description':'Focus 1 error','access':'R'},
                'Focus 2 error':{'ASCII string':'F2', 'description':'Focus 2 error','access':'R'},
        }
    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass
    
    def connect(self, port=None):

        if port is not None:
            self.port = port        
        if self.port in self.devices:
          
            self.inst = self.rm.open_resource(self.port, baud_rate=self.communication["BAUDRATE"])
            self.inst.write_termination = '\r'
            self.id = self.inst.query('*IDN?')

            self.connected = True





    def disconnect(self):
        self.inst.close()
        self.connected = False
        
    @classmethod
    def _pad_payload(cls, payload, command):
        if payload != '?' and payload != '':
            factor = cls.commands[command]['scale factor']
            value = str(int(payload*factor))
        else:
            value = payload
        return value
        
    #The function recieves a command (dict) and a payload (int or str) and returns the message to be sent to the device
    def build_message(self,command, payload):
        acsii_string = command['ASCII string']
        payload = self._pad_payload(payload, command)
        message = acsii_string+payload
        return message
        
    def send_message(self, command, paylooad):
        message = self.build_message(command, paylooad)
        self.inst.write(message)  
        response = self.read_message()
        return response

    def read_message(self):
        
        full_response = self.inst.read()
        response_list = full_response.split(' ')
        if len(response_list) == 2:
            payload = response_list[1].split('\r')[0]
        else:
            payload = response_list[0].split('\r')[0]
        

        return payload
    
    def get_parameter(self, parameter_name: str):
        self.inst.read()
        
        response = self.send_message(self.commands[parameter_name], '?')

        return response

    
    def set_parameter(self, parameter_name: str, value):
        pass
