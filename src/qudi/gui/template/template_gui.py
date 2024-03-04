# -*- coding: utf-8 -*-

__all__ = ['TemplateGui']

from PySide2 import QtCore

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.gui.template.template_main_window import TemplateMainWindow


# qudi GUI measurement modules must inherit qudi.core.module.GuiBase or other GUI modules.
class TemplateGui(GuiBase):
    """ This is a simple template GUI measurement module for qudi """
    # Signal declaration for outgoing control signals to logic
    sigAddToCounter = QtCore.Signal(int)  # add an integer value to the counter value

    # Connector declaration for a logic module to interact with
    _template_logic = Connector(name='template_logic', interface='TemplateLogic')

    # Declare static parameters that can/must be declared in the qudi configuration
    # _my_config_option = ConfigOption(name='my_config_option', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def on_activate(self) -> None:
        # initialize the main window
        self._mw = TemplateMainWindow()
        self._mw.count_spinbox.setValue(self._template_logic().counter_value)
        # connect all GUI internal signals
        self._mw.sub_ten_button.clicked.connect(self._subtract_ten)
        self._mw.add_ten_button.clicked.connect(self._add_ten)
        # Connect all signals to and from the logic. Make sure the connections are QueuedConnection.
        self.sigAddToCounter.connect(
            self._template_logic().add_to_counter, QtCore.Qt.QueuedConnection
        )
        self._mw.reset_button.clicked.connect(
            self._template_logic().reset_counter, QtCore.Qt.QueuedConnection
        )
        self._template_logic().sigCounterUpdated.connect(
            self._mw.count_spinbox.setValue, QtCore.Qt.QueuedConnection
        )
        # Show the main window and raise it above all others
        self.show()

    def on_deactivate(self) -> None:
        # Disconnect all connections done in "on_activate"
        self._template_logic().sigCounterUpdated.disconnect(self._mw.count_spinbox.setValue)
        # Use "plain" disconnects (without argument) only on signals owned by this module
        self._mw.reset_button.clicked.disconnect()
        self.sigAddToCounter.disconnect()
        self._mw.add_ten_button.clicked.disconnect()
        self._mw.sub_ten_button.clicked.disconnect()
        # Close main window
        self._mw.close()

    def show(self) -> None:
        """ Mandatory method to show the main window """
        self._mw.show()
        self._mw.raise_()

    def _subtract_ten(self) -> None:
        """ Qt slot to be called upon "-10" button press """
        self.sigAddToCounter.emit(-10)

    def _add_ten(self) -> None:
        """ Qt slot to be called upon "+10" button press """
        self.sigAddToCounter.emit(10)
