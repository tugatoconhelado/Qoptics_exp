from qudi.util.uic import loadUi
from PySide2.QtWidgets import QDialog, QMainWindow, QVBoxLayout
from PySide2.QtCore import Slot, Signal, Qt
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class TCSPCMainWindow(QMainWindow):

    set_parameter_signal = Signal(str, float or int or str or bool)


    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\tcspc\tcspc.ui',
            self
        )

        self.parameters_editor = TCSPC_parameters_editor(self)
        self.system_parameters_action.triggered.connect(self.parameters_editor.show, Qt.QueuedConnection)

        self.time_combobox.currentIndexChanged.connect(self.time_stackedwidget.setCurrentIndex, Qt.QueuedConnection)
        self.tac_combobox.currentIndexChanged.connect(self.tac_stackedwidget.setCurrentIndex, Qt.QueuedConnection)
        self.sync_combobox.currentIndexChanged.connect(self.sync_stackedwidget.setCurrentIndex, Qt.QueuedConnection)
        self.cfd_combobox.currentIndexChanged.connect(self.cfd_stackedwidget.setCurrentIndex, Qt.QueuedConnection)

        self.collection_time_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.display_time_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.repeat_time_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)

        self.tac_range_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.tac_gain_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.tac_offset_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.tac_limit_high_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.tac_limit_low_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)

        self.sync_zc_level_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.sync_freq_div_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.sync_threshold_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)

        self.cfd_limit_low_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)
        self.cfd_zc_level_spinbox.valueChanged.connect(self.set_parameter, Qt.QueuedConnection)

        self.configure_plots()

    def configure_plots(self):
        
        self.counts_histogram_plot.setLabel('left', 'Counts')
        self.counts_histogram_plot.setLabel('bottom', 'Time (ns)')
        self.counts_histogram_plot.showGrid(x=True, y=True)

        self.counts_histogram_dataline = self.counts_histogram_plot.plot(pen='r')

        self.counts_plot_figure = plt.figure()
        self.counts_plot_canvas = FigureCanvasQTAgg(self.counts_plot_figure)
        self.counts_layout.addWidget(self.counts_plot_canvas)

        self.counts_plot_ax = self.counts_plot_figure.add_subplot(111)

        self.counts_plot_ax.set_facecolor('#302e2f')
        self.counts_plot_ax.xaxis.label.set_color('#b3aca9')
        self.counts_plot_ax.yaxis.label.set_color('#b3aca9')
        self.counts_plot_ax.tick_params(axis='x', colors='#b3aca9')
        self.counts_plot_ax.tick_params(axis='y', colors='#b3aca9')
        self.counts_plot_ax.spines['bottom'].set_color('#b3aca9')
        self.counts_plot_ax.spines['top'].set_color('#b3aca9')
        self.counts_plot_ax.spines['right'].set_color('#b3aca9')
        self.counts_plot_ax.spines['left'].set_color('#b3aca9')
        self.counts_plot_figure.set_facecolor('#302e2f')

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

        self.counts_plot_rects = self.counts_plot_ax.bar(self.rates_labels, y_values, width=0.6, color='green')
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

        spinbox_name = param + '_spinbox'
        spinbox = getattr(self, spinbox_name, None)
        if spinbox is not None:
            spinbox.setValue(value)
        self.parameters_editor.update_parameter(param, value)

    @Slot()
    def set_parameter(self):

        sender = self.sender()
        parameter = sender.objectName().split('_spinbox')[0]
        value = sender.value()
        if sender is not None and parameter is not None:
            self.set_parameter_signal.emit(parameter, value)

    @Slot(tuple)
    def update_rates(self, rates):

        value_str = ""
        for i in range(len(rates)):
            value_str += self.rates_labels[i] + ": " + str("{:.2e}".format(int(rates[i]))) + "\n"
        self.value_text.set_text(value_str)
        for rect, new_height in zip(self.counts_plot_rects, rates):
            rect.set_height(new_height)
        self.counts_plot_canvas.draw()

    @Slot(np.ndarray)
    def update_data(self, data):
        
        self.counts_histogram_dataline.setData(data)

class TCSPC_parameters_editor(QDialog):

    change_params_signal = Signal(dict)
    get_params_signal = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(r'C:\EXP\python\Qoptics_exp\src\qudi\gui\tcspc\tcsps_system_parameters.ui', self)

        self._current_values = self.get_parameters()

    def get_parameters(self):
    
        # Uses the sames keys as the TCSPC config itself
        parameter_dict = {
            'tac_range': self.tac_range_spinbox.value(),
            'tac_gain': self.tac_gain_spinbox.value(),
            'tac_offset': self.tac_offset_spinbox.value(),
            'tac_limit_high': self.tac_limit_high_spinbox.value(),
            'tac_limit_low': self.tac_limit_low_spinbox.value(),
    
            'collect_time': self.collection_time_spinbox.value(),
            'repeat_time': self.repeat_time_spinbox.value(),
            'display_time': self.display_time_spinbox.value(),
        
            'sync_zc_level': self.sync_zc_level_spinbox.value(),
            'sync_freq_div': self.sync_freq_divider_spinbox.value(),
            'sync_threshold': self.sync_threshold_spinbox.value(),
        
            'cfd_limit_low': self.cfd_limit_low_spinbox.value(),
            'cfd_zc_level': self.cfd_zc_level_spinbox.value()
        }
        return parameter_dict
    
    def accept(self):

        self._current_values = self.get_parameters()
        print(self._current_values)
        self.change_params_signal.emit(self._current_values)
        super().accept()

    def reject(self):

        self.get_params_signal.emit(self._current_values)
        super().reject()

    @Slot(dict)
    def update_values(self, new_values):

        print(new_values)
        self.tac_range_spinbox.setValue(new_values['tac_range'])
        self.tac_gain_spinbox.setValue(new_values['tac_gain'])
        self.tac_offset_spinbox.setValue(new_values['tac_offset'])
        self.tac_limit_high_spinbox.setValue(new_values['tac_limit_high'])
        self.tac_limit_low_spinbox.setValue(new_values['tac_limit_low'])

        self.collection_time_spinbox.setValue(new_values['collect_time'])
        self.repeat_time_spinbox.setValue(new_values['repeat_time'])
        self.display_time_spinbox.setValue(new_values['display_time'])

        self.sync_zc_level_spinbox.setValue(new_values['sync_zc_level'])
        self.sync_freq_divider_spinbox.setValue(new_values['sync_freq_div'])
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
