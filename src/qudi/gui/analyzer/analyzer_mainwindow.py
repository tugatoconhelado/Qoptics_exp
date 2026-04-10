from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QTableWidgetItem, QFileDialog
from PySide2.QtCore import Slot, Signal, QDir, QObject
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class AnalyzerMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    pb_output_status_signal = Signal(tuple)
    pb_output_stop_signal = Signal()
    update_channels_signal = Signal(list)
    update_pulses_signal = Signal(list)
    clear_channels_signal = Signal()
    load_seq_file_signal = Signal(str)
    save_seq_file_signal = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.join(os.path.dirname(__file__), "analyzer.ui"), self)

        self.configure_plots()

    def configure_plots(self):

        self.pulsed_exp_dataline = self.data_plot.plot([], pen='yellow')
        self.data_plot.setLabel('left', 'Counts')




if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication
    print(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    import artwork.qudi_icons_rc
    from qudi.logic.pulsed_exp_logic import Pulse

    app = QApplication(sys.argv)
    window = AnalyzerMainWindow()
    window.show()

    sys.exit(app.exec_())
