from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys


class TimeTraceMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\timetrace\timetrace.ui',
            self
        )
        self.exit_action.triggered.connect(self.close)

        self.configure_plots()
        self.run_cps_button.clicked.connect(self.req_start_timetrace)

        self.cps_label.setFont(QFont('Arial', 20))


    def configure_plots(self) -> None:
        """
        Configures the plots in the event of gui initialization

        It sets the label on the plot elements, creates dataline instances for
        the plots and sets any limits, in this case, the temporal axis can´t be
        less than 0
        """
        self.cps_plot.setBackground('black')
        self.cps_plot.setLabel('left', 'Intensity (cps)')
        self.cps_plot.setLabel('bottom', 'Time (sec)')

        self.cps_dataline = self.cps_plot.plot([], [], pen='yellow')

    @Slot()
    def req_start_timetrace(self) -> None:
        """
        Sends the `start_experiment_signal` to request the start of the
        experiment with the parameters for the acquisition."""

        samp_freq = int(self.samp_freq_spinbox.value())
        refresh_time = float(self.refresh_time_spinbox.value())
        window_time = float(self.window_time_spinbox.value())
        self.start_experiment_signal.emit(samp_freq, refresh_time, window_time)
        self.filename_label.setText('')
        self.cps_plot.setTitle('')

    @Slot(np.ndarray, np.ndarray)
    def update_plot(self, time_array: np.ndarray, counts: np.ndarray) -> None:
        """
        Updates the plots when new data is received.

        Parameters
        ----------
        time_array : np.ndarray
            Array containing the x axis values corresponding to time in secs.
        counts : np.ndarray
            Array containing the y axis values corresponding to counts in cps.
        """
        self.cps_dataline.setData(time_array, counts)
        self.cps_label.setText(str(round(counts[-1])))
        self.mean_label.setText(str(round(np.mean(counts))))
        self.std_label.setText(str(round(np.std(counts), 2)))

    #@Slot(data_timetrace.TimeTraceData, str)
    #def update_on_data_loaded(self, data, filename):

    #    self.update_plot(data.time_array, data.counts)
    #    self.filename_label.setText(filename)
    #    self.cps_plot.setTitle(filename, **{'size': '7pt'})


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = TimeTraceMainWindow()
    widget.show()
    sys.exit(app.exec_())