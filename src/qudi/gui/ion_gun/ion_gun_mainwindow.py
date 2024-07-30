from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import sys
import os
import numpy as np


class IonGunMainWindow(QMainWindow):

    conect_signal = Signal(str)
    parameter_signal = Signal(str)
    get_parameter_for_setter_signal = Signal(str)
    set_parameter_signal = Signal(str, float)
    no_parameter_signal = Signal(str)

    commands = {'Remote enable':{'ASCII string':'RE', 'description':'Remote enable','access':'NP'},
                'Local':{'ASCII string':'LO', 'description':'Local','access':'NP'},
                'Enabl local':{'ASCII string':'EN', 'description':'Enable local','access':'NP'},
                'Operate':{'ASCII string':'OP', 'description':'Operate','access':'NP'},
                'Standby':{'ASCII string':'SB', 'description':'Standby','access':'NP'},
                'Degas':{'ASCII string':'DG', 'description':'Degas','access':'NP'},
                'Off':{'ASCII string':'OF', 'description':'Off','access':'NP'},
                'Reset powe unit':{'ASCII string':'RSE', 'description':'Reset power unit','access':'NP'},
                'HV on':{'ASCII string':'HE', 'description':'High Voltage on','access':'NP'},
                'HV off':{'ASCII string':'HA', 'description':'High Voltage off','access':'NP'},
                'Operating status':{'ASCII string':'OS', 'description':'Operating status','access':'NP'},
                'Error status':{'ASCII string':'ES', 'description':'Error status','access':'R'},
                'Emision current':{'ASCII string':'EC', 'description':'Emision current','access':'RW', 'min':10, 'max':10000, 'scale factor':0.1, 'unit':'µA'},
                'Energy':{'ASCII string':'EN', 'description':'Energy','access':'RW', 'min':0, 'max':5000, 'scale factor':1, 'unit':'eV'},
                'Extractor voltage':{'ASCII string':'EX', 'description':'Extractor voltage','access':'RW', 'min':60, 'max':100, 'scale factor':100, 'unit':'%'},
                'Focus 1 voltage':{'ASCII string':'F1', 'description':'Focus 1 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit':'%'},
                'Focus 2 voltage':{'ASCII string':'F2', 'description':'Focus 2 voltage','access':'RW', 'min':0, 'max':100, 'scale factor':100, 'unit':'%'},
                'Position X':{'ASCII string':'X0', 'description':'Position X','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit':'µA'},
                'Position Y':{'ASCII string':'Y0', 'description':'Position Y','access':'RW', 'min':-5000, 'max':5000, 'scale factor':0.1, 'unit':'µA'},
                'Width X':{'ASCII string':'WX', 'description':'Width X','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit':'µA'},
                'Width Y':{'ASCII string':'WY', 'description':'Width Y','access':'RW', 'min':0, 'max':10000, 'scale factor':0.01, 'unit':'µA'},
                'Blanking X':{'ASCII string':'BX', 'description':'Blanking X','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit':'%'},
                'Blanking Y':{'ASCII string':'BY', 'description':'Blanking Y','access':'RW', 'min':1, 'max':30, 'scale factor':1, 'unit':'%'},
                'Blanking level':{'ASCII string':'BL', 'description':'Blanking level','access':'RW', 'min':0, 'max':1, 'scale factor':1, 'unit':''},
                'Time per dot':{'ASCII string':'TD', 'description':'Time per dot','access':'RW', 'min':30, 'max':30000, 'scale factor':1, 'unit':'µs'},
                'Angle phi':{'ASCII string':'PH', 'description':'Angle phi','access':'RW', 'min':-90, 'max':90, 'scale factor':1, 'unit':'°'},
                'Angle theta':{'ASCII string':'TH', 'description':'Angle theta','access':'RW', 'min':-85, 'max':85, 'scale factor':1, 'unit':'°'},
                'L': {'ASCII string':'L', 'description':'lenght L','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit':'µm'},
                'D': {'ASCII string':'D', 'description':'diameter D','access':'RW', 'min':100, 'max':99900, 'scale factor':0.01, 'unit':'µm'},
                'Deflection X':{'ASCII string':'VX', 'description':'Deflection X','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit':'V/°'},
                'Deflection Y':{'ASCII string':'VY', 'description':'Deflection Y','access':'RW', 'min':1, 'max':200, 'scale factor':1, 'unit':'V/°'},
                'Energy current':{'ASCII string':'ENI', 'description':'Energy current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Energy module temperature':{'ASCII string':'ENT', 'description':'Energy module temperature','access':'R', 'scale factor':1, 'unit':'°C'},
                'Extractor current':{'ASCII string':'exi', 'description':'Extractor current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus 1 current':{'ASCII string':'f1i', 'description':'Focus 1 current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus 2 current':{'ASCII string':'f2i', 'description':'Focus 2 current','access':'R', 'scale factor':1, 'unit':'µA'},
                'Focus module temperature':{'ASCII string':'f1t', 'description':'Focus 1 module temperature','access':'R', 'scale factor':1, 'unit':'°C'},
                'Filament voltage':{'ASCII string':'FU', 'description':'Filament voltage','access':'R', 'scale factor':1, 'unit':'V'},
                'Filament current':{'ASCII string':'FI', 'description':'Filament current','access':'R', 'scale factor':10, 'unit':'A'},
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'ion_gun.ui'),
            self
        )

        self.connect_button.clicked.connect(self.req_connect)
        self.parameter_box.currentIndexChanged.connect(self.req_parameter)
        self.parameter_set_box.currentIndexChanged.connect(self.update_setter)
        self.set_button.clicked.connect(self.set_parameter)
        self.control_radios = [self.radio_remote, self.radio_local]
        self.mode_radios = [self.radio_operate, self.radio_standby, self.radio_degas, self.radio_off]
        self.high_voltage_radios = [self.radio_hv_on, self.radio_hv_off]
        for radio in self.control_radios:
            radio.toggled.connect(self.req_control)
        
        for radio in self.mode_radios:
            radio.toggled.connect(self.req_mode)

        for radio in self.high_voltage_radios:
            radio.toggled.connect(self.req_high_voltage)

    @Slot()
    def req_control(self) -> None:
        for radio in self.control_radios:
            if radio.isChecked():
                current_radio = radio
        for radio in self.control_radios:
            if radio != current_radio:
                radio.setChecked(False) 
        self.no_parameter_signal.emit(current_radio.text())


    @Slot()
    def req_mode(self) -> None:
        for radio in self.mode_radios:
            if radio.isChecked():
                current_radio = radio
        for radio in self.mode_radios:
            if radio != current_radio:
                radio.setChecked(False)
        self.no_parameter_signal.emit(current_radio.text())
    
    @Slot()
    def req_high_voltage(self) -> None:
        for radio in self.high_voltage_radios:
            if radio.isChecked():
                current_radio = radio
        for radio in self.high_voltage_radios:
            if radio != current_radio:
                radio.setChecked(False)
        self.no_parameter_signal.emit(current_radio.text())
                



    @Slot(list)
    def refresh_ports(self, list_ports: list) -> None:
        self.ports_box.clear()
        self.ports_box.addItems(list_ports)
    
    @Slot()
    def unlock_connect(self) -> None:
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

    @Slot()
    def lock_connect(self) -> None:
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)

    @Slot()
    def req_connect(self) -> None:
        self.conect_signal.emit(self.ports_box.currentText())

    @Slot()
    def create_parameter_combo_box(self) -> None:
        self.parameter_box.clear()
        for key in self.commands.keys():
            if self.commands[key]['access'] == 'RW' or self.commands[key]['access'] == 'R':
                self.parameter_box.addItem(key)
            if self.commands[key]['access'] == 'RW':
                self.parameter_set_box.addItem(key)

        
    @Slot()
    def req_parameter(self) -> None:
        self.parameter_signal.emit(self.parameter_box.currentText())

    @Slot(str, str)
    def update_parameter(self, parameter: str, description: str) -> None:

        self.parameter_value.setText(parameter)
        self.parameter_value.setToolTip(description)

    @Slot()
    def update_setter(self) -> None:
        max_value = self.commands[self.parameter_set_box.currentText()]['max']
        min_value = self.commands[self.parameter_set_box.currentText()]['min']

        if self.commands[self.parameter_set_box.currentText()]['max'] != None:
            self.setter_spin_box.setMaximum(max_value)
            self.setter_spin_box.setMinimum(min_value)
            
            #self.get_parameter_for_setter_signal.emit(self.parameter_set_box.currentText())
            
        
    @Slot(float)
    def update_parameter_for_setter(self, value: float) -> None:
        if value != -1:
            self.setter_spin_box.setValue(value)
        else:
            self.setter_spin_box.setValue(0)

    @Slot(float)
    def set_parameter(self) -> None:
        value = self.setter_spin_box.value()
        self.set_parameter_signal.emit(self.parameter_set_box.currentText(), value)


    

if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    w = IonGunMainWindow()
    w.show()
    w.raise_()
    sys.exit(app.exec_())