from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.confocal.tracking_widget import TrackingWidget
from qudi.gui.confocal.confocal_widget import ConfocalWidget
from qudi.gui.confocal.position_control_widget import PositionControlWidget
from qudi.util.widgets.scientific_spinbox import ScienDSpinBox
import numpy as np
import pyqtgraph as pg
import sys
import os


class ODMRMainWindow(QMainWindow):

    freq_signal = Signal(float)
    mod_span_signal = Signal(float)
    ampl_signal = Signal(float)
    phase_signal = Signal(int)
    mod_rate_signal = Signal(float)
    modulation_signal = Signal(int)
    modulation_type_signal = Signal(int)
    modulation_function_signal = Signal(int)
    display_signal = Signal(int)
    outputs_enabled_signal = Signal(int, int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'newodmr.ui'),
            self
        )

        self.signal_generator_connection = SignalGeneratorConnection()

        self.freq_spinbox.lineEdit().returnPressed.connect(self._on_freq_changed)
        self.mod_span_spinbox.lineEdit().returnPressed.connect(self._on_mod_span_changed)
        self.mod_rate_spinbox.lineEdit().returnPressed.connect(self._on_mod_rate_changed)
        self.phase_spinbox.lineEdit().returnPressed.connect(self._on_phase_changed)
        self.ampl_spinbox.lineEdit().returnPressed.connect(self._on_ampl_changed)

        self.modulation_on_radiobutton.toggled.connect(self._on_modulation_toggled)
        self.modulation_type_combobox.currentIndexChanged.connect(self._on_modulation_type_changed)
        self.modulation_function_combobox.currentIndexChanged.connect(self._on_modulation_function_changed)
        self.display_combobox.currentIndexChanged.connect(self._on_display_changed)

        self.lf_radiobutton.toggled.connect(self._on_output_changed)
        self.rf_radiobutton.toggled.connect(self._on_output_changed)
        self.rf_doubler_radiobutton.toggled.connect(self._on_output_changed)

        self.configure_plots()

    @Slot(int, int, int)
    def set_outputs(self, rf, rf_doubler, lf):
        self.rf_radiobutton.setChecked(rf)
        self.rf_doubler_radiobutton.setChecked(rf_doubler)
        self.lf_radiobutton.setChecked(lf)

    @Slot(bool)
    def _on_output_changed(self, checked):
        self.outputs_enabled_signal.emit(
            int(self.rf_radiobutton.isChecked()),
            int(self.rf_doubler_radiobutton.isChecked()),
            int(self.lf_radiobutton.isChecked()),
        )

    @Slot(int)
    def _on_display_changed(self, index):
        self.display_signal.emit(index)

    @Slot()
    def _on_freq_changed(self):
        print(self.freq_spinbox.value())
        self.freq_signal.emit(float(self.freq_spinbox.value()))

    @Slot()
    def _on_mod_span_changed(self):
        self.mod_span_signal.emit(self.mod_span_spinbox.value())

    @Slot()
    def _on_mod_rate_changed(self):
        self.mod_rate_signal.emit(self.mod_rate_spinbox.value())

    @Slot()
    def _on_phase_changed(self):
        self.phase_signal.emit(self.phase_spinbox.value())

    @Slot()
    def _on_ampl_changed(self):
        self.ampl_signal.emit(self.ampl_spinbox.value())

    @Slot(bool)
    def _on_modulation_toggled(self, checked):
        if checked is True:
            checked = 1
        elif checked is False:
            checked = 0
        self.modulation_signal.emit(checked)

    @Slot(int)
    def _on_modulation_type_changed(self, index):
        print(index)
        self.modulation_type_signal.emit(index)

    @Slot(int)
    def _on_modulation_function_changed(self, index):
        self.modulation_function_signal.emit(index)

    def configure_plots(self):

        self.odmr_dataline = self.odmr_plot.plot([1, 2, 3, 4], [1, 4, 9, 16], pen='yellow')

        self.odmr_plot.setLabel('bottom', 'Frequency (GHz)')
        self.odmr_plot.setLabel('left', 'Intensity (A.U.)')

    def update_odmr_plot(self, x, y):
        self.odmr_dataline.setData(x, y)


class SignalGeneratorConnection(QWidget):

    connect_signal = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\odmr\sg_connect.ui',
            self
        )

        self.connect_button.clicked.connect(self._on_connect_button_clicked)

    def _on_connect_button_clicked(self):
        print(self.devices_combobox.currentText())
        self.connect_signal.emit(self.devices_combobox.currentText())

    @Slot(list)
    def update_device_list(self, devices: list):
        self.devices_combobox.clear()
        self.devices_combobox.addItems(devices)

    def show(self):
        super().show()
        self.refresh_button.clicked.emit()


if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    main = ODMRMainWindow()
    main.show()
    sys.exit(app.exec_())