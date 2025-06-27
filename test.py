import nidaqmx
import time
import keyboard


def test_func():

    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan("Dev2/port1/line1")
        task.start()
        dt = 0.001
        
        task.write(False)

    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan("Dev2/port0/line1")
        task.start()
        dt = 0.001
        
        for i in range(1600):
            task.write(True)
            time.sleep(dt)
            task.write(False)
            time.sleep(dt)

            #keyboard interrupt
            if keyboard.is_pressed('q'):
                break
            print(f'loop {i}')

    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan("Dev2/port0/line1")
        task.start()
        dt = 0.001
        
        task.write(True)

def test_func2():
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan("Dev2/AO0", min_val=0, max_val=5)
        task.start()
        dt = 0.0005
        
        for i in range(1600):
            task.write(5.0)
            time.sleep(dt)
            task.write(0.0)
            time.sleep(dt)

            #keyboard interrupt
            if keyboard.is_pressed('q'):
                break
            print(f'loop {i}')


test_func()