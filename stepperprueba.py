import sys  # We need sys so that we can pass argv to QApplication
import os
import nidaqmx
from nidaqmx.constants import LineGrouping
import numpy as np
from datetime import datetime
import csv
import time

#Nidaqmx reference help
#https://nidaqmx-python.readthedocs.io/en/latest/

#PyQt reference help
#https://www.tutorialspoint.com/pyqt/pyqt_basic_widgets.htm

#Number of steps for entire range: 79974 (500 mm)

def __init__(self, *args, **kwargs):
    super(self).__init__(*args, **kwargs)

    self.Dev = 'Dev2'
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

    Device = self.Dev + '/port1/line1:3'
    #DeviceDI = self.Dev + '/port1/line0:1'

#    with nidaqmx.Task() as taskDI:
#       taskDI.di_channels.add_di_chan(DeviceDI)
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(Device)
        port1 = 0*(2**2) + (1-direction)/2*(2**1) + 1*(2**0)
        port = int(2**2 + port1)
        port1 = int(port1)
        print('port1', port1)
        task.write(port1)
        task.start()
        halfDt = 0.0001

    print('done')

def initiateStepperMotor(self):
    print('Initiating Stepper Motors...')

    Device = self.Dev + '/port1/line1:3'
    
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(Device)
        port1 = 0
        task.write(port1)
        task.stop()

    print('done')

def setStep(self):
    print('set Step')

def setToZero(self):
    print('set to zero')
    self.stepNumber = 0
        
def stop(self):
    print('stopping...')
    self.bStop = 1

