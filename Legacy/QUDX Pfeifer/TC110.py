import pyvisa as visa
from pyvisa.constants import StopBits, Parity
import logging
logging.basicConfig(filename='TC110.log', encoding='utf-8', level=logging.WARNING)
from time import sleep
from dict_TC110 import commands, data_types

class TC110:
    def __init__(self, device_id=1, port=None, autoconnect=True):
        self.device_id = self._format_id(device_id)
        self.communication = {'BAUDRATE' : 9600,
                              'DATA_BITS' : 8,
                              'PARITY' : Parity.none,
                              'START_BITS' : 1,
                              'STOP_BITS' : StopBits.one}
        self.rm = visa.ResourceManager('@py')
        self.devices = self.rm.list_resources()
        if port == None:
            if len(self.devices)>0:
                self.port = self.devices[0]
                print(f'port set to {self.port}')
            else:
                raise Exception('No device connected or not de-initialized. Try connecting/turning on the pump or restarting the python kernel.')
        else:
            self.port = port
    
    def connect(self, device_id=1, port=None):
        if port is not None:
            self.port = port        
        self.device_id = self._format_id(device_id)
        if self.port in self.devices:
            self.inst = self.rm.open_resource(self.port, baud_rate=self.communication["BAUDRATE"], data_bits=self.communication["DATA_BITS"], parity=self.communication["PARITY"], stop_bits=self.communication["STOP_BITS"])
            self.inst.write_termination = '\r'
            # try communicating and try other ports in self.devices if unsuccessful. If all fails, raise Exception('No Pfeiffer device found.').
        else:
            raise Exception('No Pfeiffer device found.')
        
    @classmethod
    def _pad_payload(cls, payload, length):
        payload = str(payload)
        if len(payload) >= length:
            return payload
        else:
            return cls._pad_payload('0'+payload, length)
    @classmethod
    def _format_id(cls, id):
        if type(id) not in [str,int]:
            raise TypeError(f'ID should be an integer between 1 and 255. {type(id)} was given.')
        if int(id) > 255 or int(id) < 1:
            raise ValueError(f'ID should be an integer between 1 and 255. {id} was given.')
        formatted_id = cls._pad_payload(str(int(id)),3)
        return formatted_id
    @classmethod
    def _calculate_checksum(cls, message_string):
        #Could also just attempt conversion with message_string = str(message_string)
        if type(message_string)==str:
            checksum = cls._pad_payload(str(sum(message_string.encode('ascii')) % 256),3)
            return checksum
        else:
            raise TypeError(f'Expected input of type string but received {type(message_string)}.')
    @classmethod
    def _received_ok(cls, received_string):
        if type(received_string)==str:
            bool_result = cls._calculate_checksum(received_string[:-3])==received_string[-3:]
        else:
            raise TypeError(f'Expected input of type string but received {type(received_string)}.')
        return bool_result
    
    @staticmethod
    def cast(payload,command):
        data_type = command["data type"]
        if command["data type"] == 0:
            out = bool(int(payload))
        elif command["data type"] == 1:
            out = int(payload)
        elif command["data type"] == 2:
            out = float(payload)
        elif command["data type"] == 4:
            out = str(payload)
        elif command["data type"] == 7:
            out = int(payload)
        elif command["data type"] == 11:
            out = str(payload)
        else:
            raise Exception('Unknwon data type.')
        return out
    
    def send_message(self, command, device_id=None, query_only=True, payload='=?'):
        if device_id == None:
            device_id = self.device_id
        else:
            device_id = self._format_id(device_id)
        param_number = str(command["number"])
        action = '00' if query_only else '10'
        payload_length = '02' if query_only else data_types[command["data type"]]["length"]
        message_string = device_id+action+param_number+payload_length+payload
        checksum = self._calculate_checksum(message_string)
        full_message = message_string+checksum
        logging.debug(f'Sending: {full_message}')
        self.inst.write(full_message)
        return full_message

    def receive_message(self):
        full_response = self.inst.read(termination='\r')
        print(full_response)
        logging.debug(f'Received: {full_response}')
        if not self._received_ok(full_response):
            logging.warning('Checksum error.')
            return None
        else:
            device_id = full_response[:3]
            action = full_response[3:5]
            param_number = full_response[5:8]
            payload_length = int(full_response[8:10])
            payload = full_response[10:-3]
            if payload_length != len(payload):
                logging.warning('Payload length error.')
                return None
            else:
                message = {'device_id':device_id, 'action' : action, 'param_number' : param_number, 'payload_length' : payload_length, 'payload' : payload}
                return message

    def start(self, device_id=None):
        self.send_message(command=commands["PumpgStatn"], device_id=device_id, query_only=False, payload='111111')
        message = self.receive_message()
        print(message)
    
    def stop(self, device_id=None):
        self.send_message(command=commands["PumpgStatn"], device_id=device_id, query_only=False, payload='000000')
        message = self.receive_message()
        print(message)

    def get_pressure(self, device_id=None):        
        self.send_message(command=commands["Pressure"], device_id=device_id)
        message = self.receive_message()
        print(message)
    
    def get_speed(self, device_id=None):
        self.send_message(command=commands["ActualSpd"], device_id=device_id)
        message = self.receive_message()
        print(message)
        
        
instrument = TC110()
instrument.connect()
instrument.stop()

instrument.get_speed()
