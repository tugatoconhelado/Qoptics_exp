from qudi.util.uic import loadUi
from PySide2.QtWidgets import QDialog, QMainWindow
from PySide2.QtCore import Slot, Signal, Qt
import pyqtgraph as pg
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.tcspc.tcspc_mainwindow import TCSPCMainWindow, TCSPC_parameters_editor
from qudi.logic import plot
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import functools
import os


class TCSPCGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """

    # Signal declaration for outgoing control signals to logic
    #sigAddToCounter = Signal(int)  # add an integer value to the counter value
    init_spc_signal = Signal()

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

        # connect all GUI internal signals
        self._mw.pause_button.clicked.connect(self.pause_measurement, Qt.QueuedConnection)
        self._mw.start_button.clicked.connect(self.start_measurement, Qt.QueuedConnection)
        self._mw.restart_button.clicked.connect(self.restart_measurement, Qt.QueuedConnection)

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self._mw.parameters_editor.change_params_signal.connect(
            self._tcspc_logic().set_parameters, Qt.QueuedConnection
        )
        self._mw.parameters_editor.get_params_signal.connect(
            self._tcspc_logic().get_parameters, Qt.QueuedConnection
        )

        # Measurement control functions
        self._mw.export_lifetime_action.triggered.connect(
            self.export_lifetime, Qt.QueuedConnection
        )
        self._mw.stop_button.clicked.connect(
            self._tcspc_logic().stop_measurement, Qt.QueuedConnection
        )
        self._mw.restart_button.clicked.connect(
            self._tcspc_logic().restart_measurement, Qt.QueuedConnection
        )
        self._mw.pause_button.clicked.connect(
            self._tcspc_logic().pause_measurement, Qt.QueuedConnection
        )
        self._mw.start_button.clicked.connect(
            self._tcspc_logic().start_fifo_measurement, Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            self._tcspc_logic().save_data, Qt.QueuedConnection
        )
        self._mw.save_as_action.triggered.connect(
            functools.partial(
            self._tcspc_logic().save_data_as
            ),
            Qt.QueuedConnection
        )
        self._mw.load_action.triggered.connect(
            functools.partial(
                self._tcspc_logic().load_data
            ),
            Qt.QueuedConnection
        )

        self._mw.load_button.clicked.connect(
            functools.partial(
                self._tcspc_logic().load_data
            ), Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            self._tcspc_logic().load_previous_data, Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            self._tcspc_logic().load_next_data, Qt.QueuedConnection
        )

        self._tcspc_logic().data_signal.connect(
            self._mw.update_data, Qt.QueuedConnection
        )
        self._tcspc_logic().sig_parameters.connect(
            self._mw.parameters_editor.update_values, Qt.QueuedConnection
        )
        self._tcspc_logic().sig_rate_values.connect(
            self._mw.update_rates, Qt.QueuedConnection
        )
        self._tcspc_logic().sig_parameter.connect(
            self._mw.update_parameter, Qt.QueuedConnection
        )

        self._mw.set_parameter_signal.connect(
            self._tcspc_logic().set_parameter, Qt.QueuedConnection
        )

        self._tcspc_logic().status_sig.connect(
            self._mw.update_status, Qt.QueuedConnection
        )

        self._tcspc_logic().file_changed_signal.connect(
            self.update_file_label, Qt.QueuedConnection
        )

        self._tcspc_logic().progress_signal.connect(
            self._mw.update_status_bar_progress, Qt.QueuedConnection
        )

        self._mw.previous_button.clicked.emit()
        self.init_spc_signal.connect(self._tcspc_logic().init_spc, Qt.QueuedConnection)
        self.init_spc_signal.emit()

        # Show the main window and raise it above all others
        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"

        #self._mw.parameters_editor.change_params_signal.disconnect()
        #self._mw.parameters_editor.get_params_signal.disconnect()

        self._mw.system_parameters_action.triggered.disconnect()

        self._mw.stop_button.clicked.disconnect()
        self._mw.restart_button.clicked.disconnect()
        self._mw.pause_button.clicked.disconnect()
        self._mw.start_button.clicked.disconnect()

        #self._mw.save_button.clicked.disconnect()
        #self._mw.load_button.clicked.disconnect()

        self._tcspc_logic().data_signal.disconnect()
        self._tcspc_logic().sig_parameters.disconnect()
        self._tcspc_logic().sig_rate_values.disconnect()

        # Close main window
        #self._mw.system_parameters_action.triggered.disconnect()

        self._mw.close()

    def show(self) -> None:
        """ Mandatory method to show the main window """
        self._mw.show()
        self._mw.raise_()

    def pause_measurement(self):
        self._mw.restart_button.setEnabled(True)

    def start_measurement(self):
        self._mw.restart_button.setEnabled(False)
        self._mw.counts_histogram_plot.setTitle('Measurement', **{'size': '7pt'})

    def restart_measurement(self):
        self._mw.restart_button.setEnabled(False)

    @Slot()
    def export_lifetime(self):
        
        plot.lifetime_plot(
            self._tcspc_logic().data.time_bins,
            self._tcspc_logic().data.histogram,
        )

    @Slot(str)
    def update_file_label(self, new_file: str):

        head, filename = os.path.split(new_file)
        self._mw.filename_label.setText(filename)
        self._mw.counts_histogram_plot.setTitle(filename, **{'size': '7pt'})

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