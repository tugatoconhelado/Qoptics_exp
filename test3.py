import pyvisa as visa
from pyvisa.constants import StopBits, Parity
from time import sleep
import serial
import serial.tools.list_ports

communication = {'BAUDRATE' : 1200,
                              'DATA_BITS' : 8,
                              'PARITY' : Parity.none,
                              'START_BITS' : 1,
                              'STOP_BITS' : StopBits.one}

ports = serial.tools.list_ports.comports()
ports_names = []
for port in ports:
    ports_names.append(port.device)

print(ports_names)
        
        

ser = serial.Serial('COM3', baudrate=communication["BAUDRATE"], timeout=1)
ser.write(b'*IND?\r')
print(ser.readlines())

ser.close()