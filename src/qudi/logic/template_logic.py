# -*- coding: utf-8 -*-

__all__ = ['TemplateLogic']

from PySide2 import QtCore

from qudi.core.module import LogicBase
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex


# qudi logic measurement modules must inherit qudi.core.module.LogicBase or other logic modules.
class TemplateLogic(LogicBase):
    """ This is a simple template logic measurement module for qudi.

    Example config that goes into the config file:

    example_logic:
        module.Class: 'template_logic.TemplateLogic'
        options:
            increment_interval: 2
        connect:
            template_hardware: dummy_hardware
    """

    # Declare signals to send events to other modules connecting to this module
    sigCounterUpdated = QtCore.Signal(int)  # update signal for the current integer counter value

    # Declare static parameters that can/must be declared in the qudi configuration
    _increment_interval = ConfigOption(name='increment_interval', default=1, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    _counter_value = StatusVar(name='counter_value', default=0)

    # Declare connectors to other logic modules or hardware modules to interact with
    _template_hardware = Connector(name='template_hardware',
                                   interface='TemplateInterface',
                                   optional=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()  # Mutex for access serialization

    def on_activate(self) -> None:
        # Check if _increment_interval is not too small (lower boundary is 1.5 * trigger_time)
        assert self._increment_interval >= 1.5 * self._template_hardware().trigger_time, \
            'increment_interval must be >= 1.5 * <hardware trigger time>'
        # Set up a Qt timer to send periodic signals according to _increment_interval
        self.__timer = QtCore.QTimer(parent=self)
        self.__timer.setInterval(1000 * self._increment_interval)  # Interval in milliseconds
        self.__timer.setSingleShot(False)
        # Connect timeout signal to increment slot
        self.__timer.timeout.connect(lambda: self.add_to_counter(1), QtCore.Qt.QueuedConnection)
        # Start timer
        self.__timer.start()

    def on_deactivate(self) -> None:
        # Stop timer and delete
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None

    @property
    def counter_value(self) -> int:
        with self._mutex:
            return self._counter_value

    def add_to_counter(self, value: int) -> None:
        if value != 0:
            with self._mutex:
                if value > 0:
                    hardware = self._template_hardware()
                    for i in range(value):
                        hardware.send_trigger()
                        self._counter_value += 1
                        self.sigCounterUpdated.emit(self._counter_value)
                else:
                    self._counter_value += value
                    self.sigCounterUpdated.emit(self._counter_value)

    def reset_counter(self) -> None:
        with self._mutex:
            self._counter_value = 0
            self.sigCounterUpdated.emit(self._counter_value)
