import nidaqmx
import msvcrt
import time


def moveAxisDir(direction,steps):
    #print('moving axis direction')

    Device = 'Dev2/port1/line1:3'
    DeviceDI = '/Dev2/port0/line0:1'

    with nidaqmx.Task() as taskDI:
        taskDI.di_channels.add_di_chan(DeviceDI)
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(Device)
            port0 = 0*(2**2) + (1-direction)/2*(2**1) + 1*(2**0)
            port = int(2**2 + port0)
            port0 = int(port0)
            print('port0', port0)
            print('port', port)
            task.write(port0)
            task.start()
            halfDt = 0.0001
            di = taskDI.read()
            print('Initial di: ', di)
            if di == 1 and direction == 1:
                bStop = 0
            elif di == 2 and direction == -1:
                bStop = 0
            else:
                bStop = 0       
            bStop = 0
            i = 0
            while bStop == 0 and i<steps:
                i = i + 1
                task.write(port)
                #time.sleep(halfDt)
                task.write(port0)
                #time.sleep(halfDt)
                di = taskDI.read()
                #print 'di: ', di
                if di == 1 and direction == 1:
                    print('Reaching forward end, di: ', di)
                    break
                if di == 2 and direction == -1:
                    print('Reaching backward end, di: ', di)
                    break

            print('i %i' % i)
            task.write(0)
            task.stop()
        
        taskDI.stop()

#moveAxisDir(1, 1000)

def test_func():
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan('Dev2/port1/line0:2',  line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
        task.start()
        while True:
            interval = 0.0001
            print("Press any key to exit.")
            #Retrocede solo si en ambas ocasiones DIR es True
            task.write([True, True, False])
            time.sleep(interval)
            task.write([True, True, True])
            time.sleep(interval)

            if msvcrt.kbhit(): # Check the keyboard and exit if any key pressed.
                key_stroke = msvcrt.getch()
                print(key_stroke) # will print which key is pressed.
                if key_stroke:
                    break

test_func()