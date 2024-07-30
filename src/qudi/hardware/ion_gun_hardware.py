
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import QObject, Signal
import serial
import serial.tools.list_ports
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

        self.communication = {'BAUDRATE' : 1200}
        self.ports = ports = serial.tools.list_ports.comports()
        self.devices = []
        for port in ports:
            self.devices.append(port.device)
        self.connected = False
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
                'Error status':{'ASCII string':'ES', 'description':'Error status','access':'R','unit R':'', 'unit W':''},
                'Emision current':{'ASCII string':'EC', 'description':'Emision current','access':'RW', 'min':10, 'max':10000, 'scale factor':0.1, 'unit R':'µA', 'unit W':'µA'},
                'Energy':{'ASCII string':'EN', 'description':'Energy','access':'RW', 'min':0, 'max':5000, 'scale factor':1, 'unit R':'eV', 'unit W':'eV'},
                'Extractor voltage':{'ASCII string':'EX', 'description':'Extractor voltage','access':'RW', 'min':60, 'max':100, 'scale factor':100, 'unit R':'V', 'unit W':'%'},
                'Focus 1 voltage':{'ASCII string':'F1', 'description':'Focus 1 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit R':'V', 'unit W':'%'},
                'Focus 2 voltage':{'ASCII string':'F2', 'description':'Focus 2 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit R':'V', 'unit W':'%'},
                'Position X':{'ASCII string':'X0', 'description':'Position X','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit R':'µm', 'unit W':'µm'},
                'Position Y':{'ASCII string':'Y0', 'description':'Position Y','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit R':'µm', 'unit W':'µm'},
                'Width X':{'ASCII string':'WX', 'description':'Width X','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit R':'µm', 'unit W':'µm'},
                'Width Y':{'ASCII string':'WY', 'description':'Width Y','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit R':'µm', 'unit W':'µm'},
                'Blanking X':{'ASCII string':'BX', 'description':'Blanking X','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit R':'%', 'unit W':'%'},
                'Blanking Y':{'ASCII string':'BY', 'description':'Blanking Y','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit R':'%', 'unit W':'%'},
                'Blanking level':{'ASCII string':'BL', 'description':'Blanking level','access':'RW', 'min':0, 'max':1, 'scale factor':1, 'unit R':'', 'unit W':''},
                'Time per dot':{'ASCII string':'TD', 'description':'Time per dot','access':'RW', 'min':30, 'max':30000, 'scale factor':1, 'unit R':'µs', 'unit W':'µs'},
                'Angle phi':{'ASCII string':'PH', 'description':'Angle phi','access':'RW', 'min':-90, 'max':90, 'scale factor':1, 'unit R':'°', 'unit W':'°'},
                'Angle theta':{'ASCII string':'TH', 'description':'Angle theta','access':'RW', 'min':-85, 'max':85, 'scale factor':1, 'unit R':'°', 'unit W':'°'},
                'L': {'ASCII string':'L', 'description':'lenght L','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit R':'µm', 'unit W':'µm'},
                'M': {'ASCII string':'M', 'description':'lenght M','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit R':'µm', 'unit W':'µm'},
                'Deflection X':{'ASCII string':'VX', 'description':'Deflection X','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit R':'V/°', 'unit W':'V/°'},
                'Deflection Y':{'ASCII string':'VY', 'description':'Deflection Y','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit R':'V/°', 'unit W':'V/°'},
                'Energy current':{'ASCII string':'ENI', 'description':'Energy current','access':'R', 'scale factor':1, 'unit R':'µA', 'unit W':'µA'},
                'Energy module temperature':{'ASCII string':'ENT', 'description':'Energy module temperature','access':'R', 'scale factor':1, 'unit R':'°C', 'unit W':'°C'},
                'Extractor current':{'ASCII string':'exi', 'description':'Extractor current','access':'R', 'scale factor':1, 'unit R':'µA', 'unit W':'µA'},
                'Focus 1 current':{'ASCII string':'f1i', 'description':'Focus 1 current','access':'R', 'scale factor':1, 'unit R':'µA', 'unit W':'µA'},
                'Focus 2 current':{'ASCII string':'f2i', 'description':'Focus 2 current','access':'R', 'scale factor':1, 'unit R':'µA', 'unit W':'µA'},
                'Focus module temperature':{'ASCII string':'f1t', 'description':'Focus 1 module temperature','access':'R', 'scale factor':1, 'unit R':'°C', 'unit W':'°C'},
                'Filament voltage':{'ASCII string':'FU', 'description':'Filament voltage','access':'R', 'scale factor':100, 'unit R':'V', 'unit W':'V'},
                'Filament current':{'ASCII string':'FI', 'description':'Filament current','access':'R', 'scale factor':10, 'unit R':'A', 'unit W':'A'},
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
            print('Connecting to ', self.port)
          
            self.inst = serial.Serial(self.port, baudrate= self.communication["BAUDRATE"], timeout=0.1)
            
            self.inst.write(b'*IND?\r')
            self.id = self.inst.readlines()

            if self.id != []:
                self.connected = True
            else:
                self.connected = False

       





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
        message = (acsii_string+payload+'\r').encode()
        return message
        
    def send_message(self, command, paylooad):
        message = self.build_message(command, paylooad)
        self.inst.write(message)  
        response = self.read_message(command)
        return response

    def read_message(self, command):
        
        full_response = self.inst.readlines()
        response = ''
        if command['access'] != 'NP':
            if full_response != []:
                value = full_response[0].decode().split('\r')
                value = value[0].split(' ')
                if command['ASCII string'] == 'ES':
                    value = value[0]
                    response = value[0]
                else:
                    value = value[1]
                    if command['unit R'] != command['unit W']:
                        factor = 1
                    else:  
                        factor = command['scale factor']
                
                    value = float(value)/factor
                    response = str(value) + ' ' + command['unit R']
            

            

        else:
            response = 'No response'

        return response
        
    
    def get_parameter(self, parameter_name: str):
        
        if self.connected:
            
            response = self.send_message(self.commands[parameter_name], '?')

            return response
        else:
            return None

    
    def set_parameter(self, parameter_name: str, value):
        if self.connected:
            response = self.send_message(self.commands[parameter_name], value)
            return response
        else:
            return None
