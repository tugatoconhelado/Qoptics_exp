from PyQt5.uic import loadUi
from PyQt5.QtWidgets import*
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import pyqtgraph.exporters # needed to save platted data
import sys  # We need sys so that we can pass argv to QApplication
import os
import nidaqmx
from nidaqmx.constants import LineGrouping
import numpy as np
from datetime import datetime
import csv
import time


class Control(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        loadUi("SOLController.ui", self)

        self.Dev = 'Dev1'
        self.initiateStepperMotor()

        self.forwardButton.clicked.connect(self.forward)
        self.backwardButton.clicked.connect(self.backward)
        self.stepComboBox.currentIndexChanged.connect(self.setStep)
        self.setToZeroButton.clicked.connect(self.setToZero)
        self.stopButton.clicked.connect(self.stop)

        self.Y = 0
        self.steps = 2
        self.stepNumber = 0

    def __getitem__(self,key):
        return getattr(self,key)

    def __setitem__(self, i, elem):
        setattr(self,i,elem)

       
    def forward(self):
        print('moving axis forward...')
        self.moveAxisDir('Y',+1,self.steps)

    def backward(self):
        print('moving axis backward...')
        self.moveAxisDir('Y',-1,self.steps)

    def moveAxisDir(self,axis,direction,steps):
        #print('moving axis direction')

        Device = self.Dev + '/port0/line0:2'
        DeviceDI = self.Dev + '/port1/line0:1'

        with nidaqmx.Task() as taskDI:
            taskDI.di_channels.add_di_chan(DeviceDI)
            with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(Device)
                port0 = 0*(2**2) + (1-direction)/2*(2**1) + 1*(2**0)
                port = int(2**2 + port0)
                port0 = int(port0)
                print('port0', port0)
                task.write(port0)
                task.start()
                halfDt = 0.0001
                di = taskDI.read()
                print('Initial di: ', di)
                if di == 1 and direction == 1:
                    self.bStop = 1
                elif di == 2 and direction == -1:
                    self.bStop = 1
                else:
                    self.bStop = 0        
               
                i = 0
                while self.bStop == 0 and i<steps:
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
                    app.processEvents()

                print('i %i' % i)
                self.stepNumber = self.stepNumber + direction*i
                self.position.setText('%i' % self.stepNumber)
                self['%c' %(axis)] = self['%c' %(axis)] + direction*steps
                task.write(0)
                task.stop()
           
            taskDI.stop()


        print('done')

    def initiateStepperMotor(self):
        print('Initiating Stepper Motors...')

        Device = self.Dev + '/port0/line0:2'
       
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(Device)
            port0 = 0
            task.write(port0)
            task.stop()

        print('done')

    def setStep(self):
        print('set Step')
        self.steps = int(self.stepComboBox.currentText())

    def setToZero(self):
        print('set to zero')
        self.stepNumber = 0
        self.position.setText('%i' % self.stepNumber)
           
    def stop(self):
        print('stopping...')
        self.bStop = 1

app = QApplication([])

window = Control()
window.show()
app.exec_()