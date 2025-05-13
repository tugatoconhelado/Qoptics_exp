from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
from qudi.core.module import Base
from PySide2.QtCore import Signal
import nidaqmx
import numpy as np



class PulseBlasterHardware(Base):

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        
    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

