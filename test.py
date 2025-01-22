import serial

ser = serial.Serial('COM3', 9600)
ser.write(b'100')
response = ser.readline()
print(response)