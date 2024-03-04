""" Timetrace Package containing all related to TimeTrace Experiment"""
import QuDX
logger = QuDX.get_logger_for_experiment('TimeTrace')
from .src import gui_timetrace
from .src import logic_timetrace
from .src import data_timetrace
from .timetrace import TimeTrace
from .__main__ import exec_timetrace
