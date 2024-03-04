from qudi.util.uic import loadUi
from PySide2.QtWidgets import QDialog, QMainWindow
from PySide2.QtCore import Slot
from PySide2 import QtCore
import pyqtgraph as pg
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
import numpy as np


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

        self.counts_plot.setLabel('left', 'Counts')
        self.counts_plot.showGrid(x=True, y=True)

        bargraph = pg.BarGraphItem(x=[1, 2, 3], height=[1, 1, 1], width=0.6)
        self.counts_plot.addItem(bargraph)
        y1 = [5, 5, 7]
        x = [1, 2, 3]
        bargraph.setOpts(height=y1)

        counts_plot_x_axis = self.counts_plot.getAxis('bottom')
        counts_plot_x_axis.setTicks([[(1, 'a'), (2, 'b'), (3, 'c')]])

        bargraph.setOpts(height=[10, 15, 12])

    @Slot(np.ndarray)
    def update_data(self, data):
        
        self.counts_histogram_dataline.setData(data)

class TCSPC_parameters_editor(QDialog):


    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(r'C:\EXP\python\Qoptics_exp\src\qudi\gui\tcspc\tcsps_system_parameters.ui', self)

        self._current_values = self.get_parameters()

    def get_parameters(self):
    
        parameter_dict = {
            'TAC': {
                'range': self.tac_range_spinbox.value(),
                'gain': self.tac_gain_spinbox.value(),
                'offset': self.tac_offset_spinbox.value(),
                'limit_high': self.tac_limit_high_spinbox.value(),
                'limit_low': self.tac_limit_low_spinbox.value()
            },
            'Time': {
                'collection': self.time_collection_spinbox.value(),
                'repeat': self.time_repeat_spinbox.value(),
                'display': self.time_display_spinbox.value(),
            },
            'Sync': {
                'zc_level': self.sync_zc_level_spinbox.value(),
                'freq_divider': self.sync_freq_divider_spinbox.value(),
                'threshold': self.sync_threshold_spinbox.value()
            },
            'CFD': {
                'limit_low': self.cfd_limit_low_spinbox.value(),
                'zc_level': self.cfd_zc_level_spinbox.value(),
            },
            'Measurement': {
                'mode': self.measurement_combobox.currentText(),
            }
        }
        return parameter_dict
    
    def accept(self):

        self._current_values = self.get_parameters()
        super().accept()

    def reject(self):

        self._update_values(self._current_values)
        super().reject()

    def _update_values(self, new_values):

        self.tac_range_spinbox.setValue(new_values['TAC']['range'])
        self.tac_gain_spinbox.setValue(new_values['TAC']['gain'])
        self.tac_offset_spinbox.setValue(new_values['TAC']['offset'])
        self.tac_limit_high_spinbox.setValue(new_values['TAC']['limit_high'])
        self.tac_limit_low_spinbox.setValue(new_values['TAC']['limit_low'])

        self.time_collection_spinbox.setValue(new_values['Time']['collection'])
        self.time_repeat_spinbox.setValue(new_values['Time']['repeat'])
        self.time_display_spinbox.setValue(new_values['Time']['display'])

        self.sync_zc_level_spinbox.setValue(new_values['Sync']['zc_level'])
        self.sync_freq_divider_spinbox.setValue(new_values['Sync']['freq_divider'])
        self.sync_threshold_spinbox.setValue(new_values['Sync']['threshold'])

        self.cfd_limit_low_spinbox.setValue(new_values['CFD']['limit_low'])
        self.cfd_zc_level_spinbox.setValue(new_values['CFD']['zc_level'])

        self.measurement_combobox.setCurrentText(new_values['Measurement']['mode'])
        
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
        
        self._mw.system_parameters_action.triggered.connect(self.parameters_editor.show)

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        #self.sigAddToCounter.connect(
        #    self._template_logic().add_to_counter, QtCore.Qt.QueuedConnection
        #)
        self._mw.stop_button.clicked.connect(
            self._tcspc_logic().stop_measurement, QtCore.Qt.QueuedConnection
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