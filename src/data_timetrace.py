import numpy as np
import dataclasses
from QuDX.core import ExperimentData
import logging


@dataclasses.dataclass
class TimeTraceParameterData:
    """
    Contains the parameters of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    sampling_frequency : int
    refresh_time : float
    window_time : float
    """
    sampling_frequency: int = 1000
    refresh_time: float = 0.1
    window_time: float = 10.0


@dataclasses.dataclass
class TimeTraceData(ExperimentData):
    """
    Contains the data of a `TimeTrace` experiment measurement.

    Attributes
    ----------
    parameters : TimeTraceParameterData
    counts : numpy.ndarray
    time_array : numpy.ndarray
    """
    parameters: TimeTraceParameterData = None
    counts: np.ndarray = None
    time_array: np.ndarray = None


if __name__ == '__main__':

    def handle_parameter_changed(obj):
        print(obj)

    pdata = TimeTraceParameterData(1000, 0.1, 5)
    ttdata = TimeTraceData(pdata, np.array([2,2,2]), np.array([1,1,1]))
    pdata.wrapper.dataChanged.connect(handle_parameter_changed)

    dict_data = {
        'sampling_frequency': 1000,
        'refresh_time': 0.02,
        'window_time': 30,
        'counts': np.array([6,7,8]),
        'time_array': np.array([0,1,2])
    }
    pdata.refresh_time = 0.01
    print(ttdata.from_dict(dict_data))
    print(ttdata.to_dict())
