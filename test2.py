import pyvisa
pyvisa.log_to_screen()
rm = pyvisa.ResourceManager()
print(rm.list_resources())