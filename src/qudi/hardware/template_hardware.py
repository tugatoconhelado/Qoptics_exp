# -*- coding: utf-8 -*-

__all__ = ['TemplateHardware']

import time

from qudi.interface.template_interface import TemplateInterface
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex


class TemplateHardware(TemplateInterface):
    """ This is a simple template hardware measurement module for qudi """

    # Declare static parameters that can/must be declared in the qudi configuration
    _trigger_time = ConfigOption(name='trigger_time', default=0.001, missing='warn')

    # Declare status variables that are saved in the AppStatus upon deactivation of the module and
    # are initialized to the saved value again upon activation.
    # _my_status_variable = StatusVar(name='my_status_variable', default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutex = Mutex()

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    @property
    def trigger_time(self) -> float:
        return self._trigger_time

    def send_trigger(self) -> None:
        with self._mutex:
            time.sleep(self._trigger_time)
