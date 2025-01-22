import os
from PySide2 import QtCore
from PySide2.QtWidgets import QDialog, QWidget, QFileDialog
from PySide2.QtCore import Slot, Qt

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow
from qudi.gui.mfield_exp.mfield_exp_mainwindow import MFieldExpMainWindow
from qudi.logic import filemanager
from qudi.logic import plot
import functools


class MFieldExpGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    
    # Declare connectors to other logic modules or hardware modules to interact with
    _mfield_exp_logic = Connector(
        name='mfield_exp_logic', interface='MFieldExpLogic')
    _magnet_hardware = Connector(
        name='magnet_hardware', interface='MagnetHardware')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:

        # initialize the main window
        self._mw = MFieldExpMainWindow()

        # connect all GUI internal signals

        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self._mw.move_signal.connect(
            self._mfield_exp_logic().move_magnet_to, Qt.QueuedConnection
        )

        self._magnet_hardware().position_changed.connect(
            self._mw.update_position, Qt.QueuedConnection
        )
        self._mw.set_zero_button.clicked.connect(
            self._magnet_hardware().set_position_as_zero, Qt.QueuedConnection
        )
        self._mw.start_mag_field_exp_signal.connect(
            self._mfield_exp_logic().start_mag_field_scan, Qt.QueuedConnection
        )

        self._mfield_exp_logic().data_signal.connect(
            self._mw.update_plot, Qt.QueuedConnection
        )
        self._mfield_exp_logic().file_changed_signal.connect(
            self.change_current_file_labels, Qt.QueuedConnection
        )

        self._mw.save_button.clicked.connect(
            functools.partial(
                self._mfield_exp_logic().save_data
            ),
            Qt.QueuedConnection
        )
        self._mw.load_button.clicked.connect(
            functools.partial(
                self._mfield_exp_logic().load_data
            ),
            Qt.QueuedConnection
        )
        self._mw.previous_button.clicked.connect(
            functools.partial(
                self._mfield_exp_logic().load_previous_data
            ),
            Qt.QueuedConnection
        )
        self._mw.next_button.clicked.connect(
            functools.partial(
                self._mfield_exp_logic().load_next_data
            ),
            Qt.QueuedConnection
        )
        self._mw.delete_button.clicked.connect(
            functools.partial(
                self._mfield_exp_logic().delete_file
            ),
            Qt.QueuedConnection
        )
        self._mw.stop_scan_button.clicked.connect(
            self._mfield_exp_logic().stop_acquisition, Qt.QueuedConnection
        )

        self._mw.previous_button.clicked.emit()
        # Show the main window and raise it above all others
        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        #self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        # Close main window
        self._mw.close()

    @Slot(str)
    def change_current_file_labels(self, filepath: str) -> None:

        head, filename = os.path.split(filepath)
        self._mw.plot_widget.setTitle(filename, **{'size': '7pt'})
        self._mw.filename_label.setText(filename)

    def show(self) -> None:
        """ Show the main window and raise it above all others """
        self._mw.show()
        self._mw.raise_()
