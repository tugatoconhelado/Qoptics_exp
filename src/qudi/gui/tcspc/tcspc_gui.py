from qudi.util.uic import loadUi
from PySide2.QtWidgets import QDialog, QMainWindow
from PySide2.QtCore import Slot
from PySide2 import QtCore
import pyqtgraph as pg
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class TCSPCMainWindow(QMainWindow):


    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\tcspc\tcspc.ui',
            self
        )

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

    change_params_signal = QtCore.Signal(dict)
    get_params_signal = QtCore.Signal(dict)

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
    
            'collect_time': self.time_collection_spinbox.value(),
            'repeat_time': self.time_repeat_spinbox.value(),
            'display_time': self.time_display_spinbox.value(),
        
            'sync_zc_level': self.sync_zc_level_spinbox.value(),
            'sync_freq_div': self.sync_freq_divider_spinbox.value(),
            'sync_threshold': self.sync_threshold_spinbox.value(),
        
            'cfd_limit_low': self.cfd_limit_low_spinbox.value(),
            'cfd_zc_level': self.cfd_zc_level_spinbox.value(),

            'mode': self.measurement_combobox.currentText(),
        }
        return parameter_dict
    
    def accept(self):

        self._current_values = self.get_parameters()
        self.change_params_signal.emit(self._current_values)
        super().accept()

    def reject(self):

        self.update_values(self._current_values)
        self.get_params_signal.emit(self._current_values)
        super().reject()

    def update_values(self, new_values):

        self.tac_range_spinbox.setValue(new_values['tac_range'])
        self.tac_gain_spinbox.setValue(new_values['tac_gain'])
        self.tac_offset_spinbox.setValue(new_values['tac_offset'])
        self.tac_limit_high_spinbox.setValue(new_values['tac_limit_high'])
        self.tac_limit_low_spinbox.setValue(new_values['tac_limit_low'])

        self.time_collection_spinbox.setValue(new_values['collect_time'])
        self.time_repeat_spinbox.setValue(new_values['repeat_time'])
        self.time_display_spinbox.setValue(new_values['display_time'])

        self.sync_zc_level_spinbox.setValue(new_values['sync_zc_level'])
        self.sync_freq_divider_spinbox.setValue(new_values['sync_freq_div'])
        self.sync_threshold_spinbox.setValue(new_values['sync_threshold'])

        self.cfd_limit_low_spinbox.setValue(new_values['cfd_limit_low'])
        self.cfd_zc_level_spinbox.setValue(new_values['cfd_zc_level'])

        self.measurement_combobox.setCurrentText(new_values['mode'])
        
        return new_values

class TCSPCGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """

    # Signal declaration for outgoing control signals to logic
    #sigAddToCounter = QtCore.Signal(int)  # add an integer value to the counter value

    # Connector declaration for a logic module to interact with
    _tcspc_logic = Connector(name='tcspc_logic', interface='TCSPCLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_activate(self) -> None:

        self.log.info('Activating TCSPC module.')
        # Initialize the main window
        self._mw = TCSPCMainWindow()

        # Initialize the parameters editor
        self.parameters_editor = TCSPC_parameters_editor(self._mw)

        # connect all GUI internal signals
        
        self._mw.system_parameters_action.triggered.connect(self.parameters_editor.show, QtCore.Qt.QueuedConnection)
        self._mw.pause_button.clicked.connect(self.pause_measurement, QtCore.Qt.QueuedConnection)
        self._mw.start_button.clicked.connect(self.start_measurement, QtCore.Qt.QueuedConnection)
        self._mw.restart_button.clicked.connect(self.restart_measurement, QtCore.Qt.QueuedConnection)

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self.parameters_editor.change_params_signal.connect(
            self._tcspc_logic().set_parameters, QtCore.Qt.QueuedConnection
        )
        self.parameters_editor.get_params_signal.connect(
            self._tcspc_logic().get_parameters, QtCore.Qt.QueuedConnection
        )

        # Measurement control functions
        self._mw.stop_button.clicked.connect(
            self._tcspc_logic().stop_measurement, QtCore.Qt.QueuedConnection
        )
        self._mw.restart_button.clicked.connect(
            self._tcspc_logic().restart_measurement, QtCore.Qt.QueuedConnection
        )
        self._mw.pause_button.clicked.connect(
            self._tcspc_logic().pause_measurement, QtCore.Qt.QueuedConnection
        )
        self._mw.start_button.clicked.connect(
            self._tcspc_logic().start_measurement, QtCore.Qt.QueuedConnection
        )
        self._mw.save_button.clicked.connect(
            self._tcspc_logic().save_data, QtCore.Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            self._tcspc_logic().load_data, QtCore.Qt.QueuedConnection
        )

        self._tcspc_logic().sig_data.connect(
            self._mw.update_data, QtCore.Qt.QueuedConnection
        )
        self._tcspc_logic().sig_parameters.connect(
            self.parameters_editor.update_values, QtCore.Qt.QueuedConnection
        )
        self._tcspc_logic().sig_rate_values.connect(
            self._mw.update_rates, QtCore.Qt.QueuedConnection
        )

        # Gets the parameters from the logic module
        self._tcspc_logic().get_parameters(self.parameters_editor.get_parameters())

        # Show the main window and raise it above all others
        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        #self._mw.reset_button.clicked.disconnect()
        #self.sigAddToCounter.disconnect()
        #self._mw.add_ten_button.clicked.disconnect()
        #self._mw.sub_ten_button.clicked.disconnect()
        # Close main window
        self._mw.system_parameters_action.triggered.disconnect()
        self._mw.close()

    def show(self) -> None:
        """ Mandatory method to show the main window """
        self._mw.show()
        self._mw.raise_()

    def pause_measurement(self):
        self._mw.restart_button.setEnabled(True)

    def start_measurement(self):
        self._mw.restart_button.setEnabled(False)

    def restart_measurement(self):
        self._mw.restart_button.setEnabled(False)

if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    form = TCSPCGui()
    form.show()
    sys.exit(app.exec_())

    #app = QApplication(sys.argv)
    #form = TCSPC_parameters_editor_gui()
    #form._mw.show()
    #sys.exit(app.exec_())