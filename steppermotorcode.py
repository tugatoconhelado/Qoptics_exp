import nidaqmx
import msvcrt
import time
from PySide2.QtCore import QTimer, QObject, Slot
from PySide2.QtWidgets import QApplication
import sys

class Motor(QObject):


    def __init__(self):
        super().__init__()
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan('Dev1/port0/line1',  line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
            task.start()

            task.write(True)    
        self.interval = 0.5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_motor)
        self.timer.setInterval(self.interval)

        self.task = nidaqmx.Task()
        self.task.do_channels.add_do_chan('Dev1/port0/line2')
        self.task.start()

        self.timer.start()

    @Slot()
    def move_motor(self):

        print('Moving motor')
        if self.status is False:
            self.task.write(True)
            self.status = True
        elif self.status is True:
            self.task.write(False)
            self.status = False

        if msvcrt.kbhit(): # Check the keyboard and exit if any key pressed.
            key_stroke = msvcrt.getch()
            print(key_stroke) # will print which key is pressed.
            if key_stroke:
                self.timer.stop()
                self.task.stop()
                return

def test_func():
 
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan('Dev1/port0/line0',  line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
        interval = 0.0005
        task.start()
        i = 0
        while True:    
            task.write(True)
            time.sleep(interval)
            task.write(False)
            time.sleep(interval)

            i += 1
            if msvcrt.kbhit(): # Check the keyboard and exit if any key pressed.
                key_stroke = msvcrt.getch()
                print(key_stroke) # will print which key is pressed.
                if key_stroke:
                    task.stop()
                    return
                

def test_func2():

    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan('Dev2/ao0', min_val=0, max_val=5)
        task.start()
        while True:
            interval = 0.1
            task.write(5)
            time.sleep(interval)
            task.write(0)
            time.sleep(interval)

            #if msvcrt.kbhit(): # Check the keyboard and exit if any key pressed.
            #    key_stroke = msvcrt.getch()
            #    print(key_stroke)
            #    break


if __name__ == '__main__':
    #app = QApplication(sys.argv)
    #sys.exit(app.exec_())
    #motor = Motor()
    test_func()
