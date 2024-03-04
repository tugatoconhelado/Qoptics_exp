import sys
import numpy as np
from QuDX.experiments.timetrace import gui_timetrace, logic_timetrace, data_timetrace, logger
from QuDX.utils import timetrace_plot
import functools
from PySide2.QtCore import QThread
from QuDX import core
import os


class TimeTrace(core.Experiment):
    """
    Models the TimeTrace experiment.

    Attributes
    ----------
    experiment : TimeTraceLogic
    gui : TimeTraceGui
    data: TimeTraceData
    file_manager : QuDX.core.loadlogic.FileManager

    Methods
    -------
    connect_gui_to_logic
        Connects the signals and events of the logic, gui and data between them.

    """
    def __init__(self) -> None:
        """
        Constructor of the TimeTrace class.

        It creates the instances of `TimeTraceLogic` `TimeTraceGui`
        `TimeTraceData` and moves `TimeTraceLogic` to a `QThread`.
        """
        super().__init__()
        logger.info('Initialising TimeTrace')
        pdata = data_timetrace.TimeTraceParameterData(
            sampling_frequency = 1000,
            refresh_time = 0.1,
            window_time = 10
        )
        self.data = data_timetrace.TimeTraceData(
            parameters=pdata,
            counts=np.array([]),
            time_array=np.array([])
        )

        self.experiment = logic_timetrace.TimeTraceExperiment(
            data=self.data
        )

        self.gui = gui_timetrace.TimeTraceGui()

        self.file_manager = core.filemanager.FileManager(
            data=self.data,
            data_dir='data',
            experiment_name='timetrace',
            exp_str='TMT',
            parent_gui=self.gui
        )

    def initialise(self) -> None:
        """ Starts thread containing experiment logic and initialises gui"""
        self.exp_thread = QThread()
        self.experiment.moveToThread(self.exp_thread)
        self.exp_thread.started.connect(self.experiment.on_thread_started)
        self.experiment.finished.connect(self.exp_thread.quit)
        self.experiment.finished.connect(self.experiment.deleteLater)
        self.exp_thread.finished.connect(self.exp_thread.deleteLater)
        self.exp_thread.start()

        self.gui.init_gui()
        self.connect_gui_to_logic()

        self.gui.show()

    def connect_gui_to_logic(self):
        """Connects all signals and events between gui, logic and data"""
        logger.debug('Connecting TimeTrace experiment to GUI')

        self.gui.close_experiment_signal.connect(
            self.experiment.close_experiment
        )

        self.experiment.data_updated.connect(
            self.gui.update_plot
        )
        self.gui.start_experiment_signal.connect(
            self.experiment.start_acquisition
        )
        self.gui.stop_button.clicked.connect(
            self.experiment.stop_acquisition
        )

        self.gui.save_button.clicked.connect(self.file_manager.save)
        self.gui.load_button.clicked.connect(self.file_manager.load)
        self.gui.previous_button.clicked.connect(self.file_manager.load_previous)
        self.gui.next_button.clicked.connect(self.file_manager.load_next)

        self.file_manager.data_loaded_signal.connect(self.gui.update_on_data_loaded)
        self.file_manager.data_saved_signal.connect(self.gui.update_on_data_loaded)

        # Loads the last file automatically
        self.gui.previous_button.clicked.emit()

    def export(self):

        timetrace_plot(
            x_data=self.data.time_array,
            counts=self.data.counts
        )

if __name__=='__main__':
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication()
    timetrace = TimeTrace()
    timetrace.initialise()
    sys.exit(app.exec_())
