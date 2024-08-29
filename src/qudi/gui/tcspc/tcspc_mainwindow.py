from qudi.util.uic import loadUi
from PySide2.QtWidgets import QDialog, QMainWindow, QVBoxLayout, QProgressBar
from PySide2.QtCore import Slot, Signal, Qt, QSize, QTimer
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from bh_spc import spcm
import os


class TCSPCMainWindow(QMainWindow):

    set_parameter_signal = Signal(str, int or float or str or bool)


    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'tcspc.ui'),
            self
        )

        self.parameters_editor = TCSPC_parameters_editor(self)
        self.system_parameters_action.triggered.connect(self.parameters_editor.show, Qt.QueuedConnection)


        self.progress_bar_timer = QTimer()
        self.progress_bar_timer.setInterval(5000)
        self.progress_bar_timer.timeout.connect(self.hide_progress_bar)

        self.set_status_bar()
        self.configure_plots()
        print(self.rates_widget.size())
        self.rates_widget.setMaximumSize(QSize(400, 400))
        print(self.rates_dockwidget.widget().size())

    def configure_plots(self):
        
        self.counts_histogram_plot.setLabel('left', 'Counts')
        self.counts_histogram_plot.setLabel('bottom', 'Time (ns)')
        self.counts_histogram_plot.showGrid(x=True, y=True)

        self.counts_histogram_dataline = self.counts_histogram_plot.plot([], [], pen='r')

        self.counts_plot_figure = plt.figure()
        self.counts_plot_canvas = FigureCanvasQTAgg(self.counts_plot_figure)
        self.counts_layout.addWidget(self.counts_plot_canvas)

        self.counts_plot_ax = self.counts_plot_figure.add_subplot(111)

        self.counts_plot_ax.set_facecolor('#000000')
        self.counts_plot_ax.xaxis.label.set_color('#b3aca9')
        self.counts_plot_ax.yaxis.label.set_color('#b3aca9')
        self.counts_plot_ax.tick_params(axis='x', colors='#b3aca9')
        self.counts_plot_ax.tick_params(axis='y', colors='#b3aca9')
        self.counts_plot_ax.spines['bottom'].set_color('#b3aca9')
        self.counts_plot_ax.spines['top'].set_color('#b3aca9')
        self.counts_plot_ax.spines['right'].set_color('#b3aca9')
        self.counts_plot_ax.spines['left'].set_color('#b3aca9')
        self.counts_plot_figure.set_facecolor('#000000')

        for item in self.counts_plot_ax.get_xticklabels():
            item.set_fontsize(8)
        for item in self.counts_plot_ax.get_yticklabels():
            item.set_fontsize(8)

        self.counts_plot_ax.grid(False)
        self.rates_labels = ['SYNC', 'CFD', 'TAC', 'ADC']
        y_values = [1e4, 1e8, 1e2, 1e7]

        self.counts_plot_ax.set_yticks([10**i for i in range(9)])
        self.counts_plot_ax.minorticks_off()
        self.counts_plot_ax.spines['top'].set_visible(False)
        self.counts_plot_ax.spines['right'].set_visible(False)
        self.counts_plot_ax.spines['left'].set_linewidth(0.5)
        self.counts_plot_ax.spines['bottom'].set_linewidth(0.5)

        self.counts_plot_rects = self.counts_plot_ax.bar(self.rates_labels, y_values, width=0.6, color='#31e30e')
        self.counts_plot_ax.set_yscale('log')

        value_str = ""
        for i in range(len(self.rates_labels)):
            value_str += self.rates_labels[i] + ": " + str(y_values[i]) + "\n"
    
        self.value_text = self.counts_plot_ax.text(
            0.8,
            0.7,
            value_str,
            horizontalalignment='center',
            verticalalignment='center',
            transform=self.counts_plot_figure.transFigure,
            color='#b3aca9',
            fontsize=9
        )

        y_values = y_values[::-1]
        for rect, new_height in zip(self.counts_plot_rects, y_values):
            rect.set_height(new_height)
        self.counts_plot_canvas.draw()

    @Slot()
    def update_parameter(self, param: str, value):

        self.parameters_editor.update_parameter(param, value)

    @Slot(tuple)
    def update_rates(self, rates):

        value_str = ""
        for i in range(len(rates)):
            value_str += self.rates_labels[i] + ": " + str("{:.2e}".format(int(rates[i]))) + "\n"
        self.value_text.set_text(value_str)
        for rect, new_height in zip(self.counts_plot_rects, rates):
            rect.set_height(new_height)
        self.counts_plot_canvas.draw()
        if rates[0] == 0.0:
            self.sync_checkbox.setChecked(False)
        else:
            self.sync_checkbox.setChecked(True)

    @Slot(np.ndarray, np.ndarray)
    def update_data(self, time_bins, histogram):
        
        self.counts_histogram_dataline.setData(time_bins, histogram)

    @Slot(spcm.MeasurementState)
    def update_status(self, status):

        if spcm.MeasurementState.ARMED in status:
            self.measurement_checkbox.setChecked(True)
        elif spcm.MeasurementState.ARMED not in status:
            self.measurement_checkbox.setChecked(False)
        if spcm.MeasurementState.FIFO_OVERFLOW in status:
            self.fifo_overflow_checkbox.setChecked(True)
        elif spcm.MeasurementState.FIFO_OVERFLOW not in status:
            self.fifo_overflow_checkbox.setChecked(False)

        self.status_log_label.setText(str(status))

    def set_status_bar(self):

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setAlignment(Qt.AlignRight)
        self.progress_bar.setFixedSize(100, 15)
        self.statusbar.addPermanentWidget(self.progress_bar)
        self.setStatusBar(self.statusbar)

        self.hide_progress_bar()

    @Slot(int, int)
    def update_status_bar_progress(self, value: int, timeout=5000) -> None:

        if value == 0:
            self.progress_bar.show()
            self.progress_bar_timer.stop()
        self.progress_bar.setValue(value)

        if value == 100:
            self.progress_bar_timer.start()

    def hide_progress_bar(self):

        self.progress_bar.hide()
        self.progress_bar_timer.stop()



class TCSPC_parameters_editor(QDialog):

    change_params_signal = Signal(dict)
    get_params_signal = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(r'C:\EXP\python\Qoptics_exp\src\qudi\gui\tcspc\tcsps_system_parameters.ui', self)

        self._current_values = self.get_parameters()
        self.buttonBox.clicked.connect(self.onbutton)

    def onbutton(self, button):

        if button.text() == 'Apply':

            self._current_values = self.get_parameters()
            self.change_params_signal.emit(self._current_values)


    def get_parameters(self):
    
        # Uses the sames keys as the TCSPC config itself
        parameter_dict = {
            'tac_range': self.tac_range_spinbox.value(),
            'tac_gain': self.tac_gain_spinbox.value(),
            'tac_offset': self.tac_offset_spinbox.value(),
            'tac_limit_high': self.tac_limit_high_spinbox.value(),
            'tac_limit_low': self.tac_limit_low_spinbox.value(),
    
            'collect_time': self.collect_time_spinbox.value(),
            'repeat_time': self.repeat_time_spinbox.value(),
            'display_time': self.display_time_spinbox.value(),
        
            'sync_zc_level': self.sync_zc_level_spinbox.value(),
            'sync_freq_div': self.sync_freq_div_spinbox.value(),
            'sync_threshold': self.sync_threshold_spinbox.value(),
        
            'cfd_limit_low': self.cfd_limit_low_spinbox.value(),
            'cfd_zc_level': self.cfd_zc_level_spinbox.value()
        }
        return parameter_dict
    
    def accept(self):

        self._current_values = self.get_parameters()
        self.change_params_signal.emit(self._current_values)
        super().accept()

    def reject(self):

        self.get_params_signal.emit(self._current_values)
        super().reject()

    @Slot(dict)
    def update_values(self, new_values):

        self.tac_range_spinbox.setValue(new_values['tac_range'])
        self.tac_gain_spinbox.setValue(new_values['tac_gain'])
        self.tac_offset_spinbox.setValue(new_values['tac_offset'])
        self.tac_limit_high_spinbox.setValue(new_values['tac_limit_high'])
        self.tac_limit_low_spinbox.setValue(new_values['tac_limit_low'])

        self.collect_time_spinbox.setValue(new_values['collect_time'])
        self.repeat_time_spinbox.setValue(new_values['repeat_time'])
        self.display_time_spinbox.setValue(new_values['display_time'])

        self.sync_zc_level_spinbox.setValue(new_values['sync_zc_level'])
        self.sync_freq_div_spinbox.setValue(new_values['sync_freq_div'])
        self.sync_threshold_spinbox.setValue(new_values['sync_threshold'])

        self.cfd_limit_low_spinbox.setValue(new_values['cfd_limit_low'])
        self.cfd_zc_level_spinbox.setValue(new_values['cfd_zc_level'])
        
        return new_values
    
    @Slot()
    def update_parameter(self, param: str, value):

        spinbox_name = param + '_spinbox'
        spinbox = getattr(self, spinbox_name, None)
        if spinbox is not None:
            spinbox.setValue(value)
    
if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    import sys
    sys.path.append('artwork')

    app = QApplication(sys.argv)
    form = TCSPCMainWindow()
    form.show()
    sys.exit(app.exec_())
