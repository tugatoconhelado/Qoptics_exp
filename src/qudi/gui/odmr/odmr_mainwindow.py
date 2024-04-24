from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QProgressBar
from PySide2.QtCore import Slot, Signal, QDir, Qt, QTimer
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.confocal.tracking_widget import TrackingWidget
from qudi.gui.confocal.confocal_widget import ConfocalWidget
from qudi.gui.confocal.position_control_widget import PositionControlWidget
import numpy as np
import pyqtgraph as pg
import sys


class ODMRMainWindow(QMainWindow):

    freq_signal = Signal(float)
    mod_span_signal = Signal(float)
    ampl_signal = Signal(float)
    phase_signal = Signal(int)
    mod_rate_signal = Signal(float)
    modulation_signal = Signal(int)
    modulation_type_signal = Signal(int)
    modulation_function_signal = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\odmr\newodmr.ui',
            self
        )

        self.freq_spinbox.lineEdit().returnPressed.connect(self._on_freq_changed)
        self.mod_span_spinbox.lineEdit().returnPressed.connect(self._on_mod_span_changed)
        self.mod_rate_spinbox.lineEdit().returnPressed.connect(self._on_mod_rate_changed)
        self.phase_spinbox.lineEdit().returnPressed.connect(self._on_phase_changed)
        self.ampl_spinbox.lineEdit().returnPressed.connect(self._on_ampl_changed)

        self.modulation_on_radiobutton.toggled.connect(self._on_modulation_toggled)
        self.modulation_type_combobox.currentIndexChanged.connect(self._on_modulation_type_changed)
        self.modulation_function_combobox.currentIndexChanged.connect(self._on_modulation_function_changed)

    @Slot()
    def _on_freq_changed(self):
        self.freq_signal.emit(self.freq_spinbox.value())

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


if __name__ == '__main__':

    sys.path.append('artwork')
    app = QApplication(sys.argv)
    main = ODMRMainWindow()
    main.show()
    sys.exit(app.exec_())