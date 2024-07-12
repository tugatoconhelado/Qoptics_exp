from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import sys
import os
import numpy as np


class PumpMainWindow(QMainWindow):

    conect_signal = Signal(str)
    parameter_signal = Signal(str)
    get_parameter_for_setter_signal = Signal(str)
    set_parameter_signal = Signal(str, float)

    data_types = {0:{'description':'False / true', 'length':'06', 'example':'000000 / 111111'},
            1:{'description':'Positive integer number', 'length':'06', 'example':'000000 to 999999'},
            2:{'description':'Positive fixed comma number', 'length':'06', 'example':'001571' 'equal to 15,71'},
            4:{'description':'Symbol chain', 'length':'06', 'example':'TC_400'},
            7:{'description':'Positive integer number', 'length':'03', 'example':'000 to 999'},
            11:{'description':'Symbol chain', 'length':'16', 'example':'BrezelBier&Wurst'}}
    commands = {'Heating': {'number': '001',  'description': 'Heating', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'Standby': {'number': '002',  'description': 'Standby', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'RUTimeCtrl': {'number': '004',  'description': 'Run-up time control', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 1, 'non-volatile': True},
            'ErrorAckn': {'number': '009',  'description': 'Error acknowledgement', 'data type': 0, 'access': 'W', 'min': 1, 'max': 1, 'default': 1, 'non-volatile': False},
            'PumpgStatn': {'number': '010',  'description': 'Pumping station', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'EnableVent': {'number': '012',  'description': 'Enable venting', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'CfgSpdSwPt': {'number': '017',  'description': 'Configuration rotation speed switch point', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'Cfg_DO2': {'number': '019',  'description': 'Configuration output DO2', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'MotorPump': {'number': '023',  'description': 'Motor pump', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 1, 'non-volatile': True},
            'Cfg_DO1': {'number': '024',  'description': ' Configuration output DO1', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 15, 'default': 0, 'non-volatile': True},
            'OpMode_BKP': {'number': '025',  'description': 'Operation mode backing pump', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 2, 'default': 0, 'non-volatile': True},
            'SpdSetMode': {'number': '026',  'description': 'Rotation speed setting mode', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'GasMode': {'number': '027',  'description': ' Gas mode', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 2, 'default': 0, 'non-volatile': True},
            'VentMode': {'number': '030',  'description': 'Venting mode', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 2, 'default': 0, 'non-volatile': True},
            'Cfg_Acc_A1': {'number': '035',  'description': 'Configuration accessory connection A1', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 8, 'default': 0, 'non-volatile': True},
            'Cfg_Acc_B1': {'number': '036',  'description': 'Configuration accessory connection B1', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 8, 'default': 1, 'non-volatile': True},
            'Cfg_Acc_A2': {'number': '037',  'description': 'Configuration accessory connection A2', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 8, 'default': 3, 'non-volatile': True},
            'Cfg_Acc_B2': {'number': '038',  'description': 'Configuration accessory connection B2', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 8, 'default': 2, 'non-volatile': True},
            'SealingGas': {'number': '050',  'description': 'Sealing gas', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'Cfg_AO1': {'number': '055',  'description': ' Configuration output AO1', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 4, 'default': 0, 'non-volatile': True},
            'CtrlViaInt': {'number': '060',  'description': 'Control via interface', 'data type': 7, 'access': 'RW', 'min': 1, 'max': 255, 'default': 1, 'non-volatile': True},
            'IntSelLckd': {'number': '061',  'description': 'Interface selection locked', 'data type': 0, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': True},
            'Cfg_DI1': {'number': '062',  'description': 'Configuration input DI1', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 6, 'default': 1, 'non-volatile': True},
            'Cfg_DI2': {'number': '063',  'description': 'Configuration input DI2', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 6, 'default': 2, 'non-volatile': True},
            'RemotePrio': {'number': '300',  'description': 'Remote priority', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'SpdSwPtAtt': {'number': '302',  'description': 'Rotation speed switch point attained', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'Error_code ': {'number': '303',  'description': 'Error code', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'OvTempElec': {'number': '304',  'description': 'Excess temperature electronic drive unit', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'OvTempPump': {'number': '305',  'description': ' Excess temperature pump', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'SetSpdAtt': {'number': '306',  'description': 'Set rotation speed attained', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'PumpAccel': {'number': '307',  'description': 'Pump accelerates', 'data type': 0, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'SetRotSpd': {'number': '308',  'description': 'Set rotation speed (Hz)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'ActualSpd': {'number': '309',  'description': 'Active rotation speed (Hz)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'DrvCurrent': {'number': '310',  'description': 'Drive current (A)', 'data type': 2, 'access': 'R', 'min': 0, 'max': 1, 'default': None, 'non-volatile': False},
            'OpHrsPump': {'number': '311',  'description': 'Operating hours pump (h)', 'data type': 2, 'access': 'R', 'min': 0, 'max': 9999.99, 'default': None, 'non-volatile': True},
            'Fw_version': {'number': '312',  'description': 'Firmware version electronic drive unit', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'DrvVoltage': {'number': '313',  'description': 'Drive voltage (V)', 'data type': 2, 'access': 'R', 'min': 0, 'max': 9999.99, 'default': None, 'non-volatile': False},
            'OpHrsElec': {'number': '314',  'description': 'Operating hours electronic drive unit (h)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 65535, 'default': None, 'non-volatile': True},
            'Nominal_Spd': {'number': '315',  'description': 'Nominal rotation speed (Hz)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'DrvPower': {'number': '316',  'description': 'Drive power (W)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'PumpCylces': {'number': '319',  'description': 'Pump cycles', 'data type': 1, 'access': 'R', 'min': 0, 'max': 65535, 'default': None, 'non-volatile': True},
            'TempElec': {'number': '326',  'description': 'Temperature electronic (°C)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'TempPmpBot': {'number': '330',  'description': 'Temperature pump bottom part (°C)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'AccelDecel': {'number': '336',  'description': 'Acceleration / Deceleration (rpm/s)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'Pressure': {'number': '340',  'description': 'Active pressure value (mbar)', 'data type': 7, 'access': 'R', 'min': 1E-10, 'max': 1E3, 'default': None, 'non-volatile': False},
            'TempBearng': {'number': '342',  'description': 'Temperature bearing (°C)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'TempMotor': {'number': '346',  'description': 'Temperature motor (°C)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'ElecName': {'number': '349',  'description': 'Name of electronic drive unit', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'Ctr_Name': {'number': '350',  'description': 'Type of display and control unit', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'Ctr_Software': {'number': '351',  'description': 'Software of display and control unit', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'HW_Version': {'number': '354',  'description': 'Hardware version electronic drive unit', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'ErrHist1': {'number': '360',  'description': 'Error code history, pos. 1', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist2': {'number': '361',  'description': 'Error code history, pos. 2', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist3': {'number': '362',  'description': 'Error code history, pos. 3', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist4': {'number': '363',  'description': 'Error code history, pos. 4', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist5': {'number': '364',  'description': 'Error code history, pos. 5', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist6': {'number': '365',  'description': 'Error code history, pos. 6', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist7': {'number': '366',  'description': 'Error code history, pos. 7', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist8': {'number': '367',  'description': 'Error code history, pos. 8', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist9': {'number': '368',  'description': 'Error code history, pos. 9', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'ErrHist10': {'number': '369',  'description': 'Error code history, pos. 10', 'data type': 4, 'access': 'R', 'min': None, 'max': None, 'default': None, 'non-volatile': True},
            'SetRotSpd_rpm': {'number': '397',  'description': 'Set rotation speed (rpm)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'ActualSpd_rpm': {'number': '398',  'description': 'Actual rotation speed (rpm)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'NominalSpd_rpm': {'number': '399',  'description': 'Nominal rotation speed (rpm)', 'data type': 1, 'access': 'R', 'min': 0, 'max': 999999, 'default': None, 'non-volatile': False},
            'RUTimeSVal': {'number': '700',  'description': 'Set value run-up time (min)', 'data type': 1, 'access': 'RW', 'min': 1, 'max': 120, 'default': 8, 'non-volatile': True},            
            'SpdSwPt1': {'number': '701',  'description': 'Rotation speed switch point 1 (%)', 'data type': 1, 'access': 'RW', 'min': 50, 'max': 97, 'default': 80, 'non-volatile': True},
            'SpdSVal': {'number': '707',  'description': 'Set value in rot. speed setting mode (%)', 'data type': 2, 'access': 'RW', 'min': 20, 'max': 100, 'default': 50, 'non-volatile': True},
            'PwrSVal': {'number': '708',  'description': 'Set value power consumption (%)', 'data type': 7, 'access': 'RW', 'min': 10, 'max': 100, 'default': 100, 'non-volatile': True},
            'SwOff BKP': {'number': '710',  'description': 'Switching off threshold backing pump in intermittend mode (W)', 'data type': 1, 'access': 'RW', 'min': 0, 'max': 1000, 'default': 0, 'non-volatile': True},
            'SwOn BKP': {'number': '711',  'description': 'Switching on threshold backing pump in intermittend mode (W)', 'data type': 1, 'access': 'RW', 'min': 0, 'max': 1000, 'default': 0, 'non-volatile': True},
            'StdbySVal': {'number': '717',  'description': 'Set value rotation speed at standby (%)', 'data type': 2, 'access': 'RW', 'min': 20, 'max': 100, 'default': 66.7, 'non-volatile': True},
            'SpdSwPt2': {'number': '719',  'description': 'Rotation speed switch point 2 (%)', 'data type': 1, 'access': 'RW', 'min': 5, 'max': 97, 'default': 20, 'non-volatile': True},
            'VentSpd': {'number': '720',  'description': 'Venting rot. speed at delayed venting (%)', 'data type': 7, 'access': 'RW', 'min': 40, 'max': 98, 'default': 50, 'non-volatile': True},
            'VentTime': {'number': '721',  'description': 'Venting time at delayed venting (s)', 'data type': 1, 'access': 'RW', 'min': 6, 'max': 3600, 'default': 3600, 'non-volatile': True},
            'Gaugetype': {'number': '738',  'description': 'Type of pressure gauge', 'data type': 4, 'access': 'RW', 'min': None, 'max': None, 'default': None, 'non-volatile': False},
            'NomSpdConf': {'number': '777',  'description': 'Nominal rotation speed confirmation (Hz)', 'data type': 1, 'access': 'RW', 'min': 0, 'max': 1500, 'default': 0, 'non-volatile': True},
            'Param_set': {'number': '794',  'description': 'Parameterset', 'data type': 7, 'access': 'RW', 'min': 0, 'max': 1, 'default': 0, 'non-volatile': False},
            'Servicelin': {'number': '795',  'description': 'Insert service line', 'data type': 7, 'access': 'RW', 'min': None, 'max': None, 'default': 795, 'non-volatile': False},
            'RS485Adr': {'number': '797',  'description': 'RS485 device address', 'data type': 1, 'access': 'RW', 'min': 1, 'max': 255, 'default': 1, 'non-volatile': True}}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'pump.ui'),
            self
        )

        self.connect_button.clicked.connect(self.req_connect)
        self.parameter_box.currentIndexChanged.connect(self.req_parameter)
        self.parameter_set_box.currentIndexChanged.connect(self.update_setter)
        self.set_button.clicked.connect(self.set_parameter)

    
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
        data_type = self.commands[self.parameter_set_box.currentText()]['data type']
        if self.commands[self.parameter_set_box.currentText()]['max'] != None:
            self.setter_spin_box.setMaximum(max_value)
            self.setter_spin_box.setMinimum(min_value)
            if data_type == 2:
                if max_value == 9999.99:
                    self.setter_spin_box.setDecimals(2)
                elif max_value == 1:
                    self.setter_spin_box.setDecimals(5)
                elif max_value == 100:
                    self.setter_spin_box.setDecimals(2)
            self.get_parameter_for_setter_signal.emit(self.parameter_set_box.currentText())
            
        
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
    w = PumpMainWindow()
    w.show()
    w.raise_()
    sys.exit(app.exec_())