from PySide2.QtWidgets import QApplication, QMainWindow, QWidget
from PySide2.QtCore import Qt, QThread, Signal, Slot, QLocale, QSize
from PySide2.QtGui import QDoubleValidator, QIntValidator, QIcon
from QuDX import core
import QuDX
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from QuDX.designer.ui import ui_timetrace
from . import data_timetrace
from QuDX.experiments.timetrace import logger


class TimeTraceGui(core.gui.ExperimentGui, ui_timetrace.Ui_timetrace):
    """
    `TimeTraceGui` contains all the front-end of the `TimeTrace` experiment.

    Attributes
    ----------
    data : TimeTraceData
        Contains the stored values of the data and the parameters.

    Methods
    -------
    init_gui
    configure_plots
    update_plot(data)
    """

    start_experiment_signal = Signal(int, float, float)
    close_experiment_signal = Signal()

    def __init__(self, parent = None):
        """ Constructor for the `TimeTraceGui` class, it calls the parent
        constructors and the `init_gui` method"""

        super().__init__(parent=parent)
        logger.debug('Creating TimeTraceGui')

    def init_gui(self) -> None:
        """
        Initializes the gui elements

        First it calls the setupUi methos of the Ui_timetrace object created
        after converting the .ui files to .py.
        It then calls the `configure_plots` methos to set up basic config of
        the plot elements.
        Sets the theme by calling the `setTheme` of the `ExperimentGui` parent
        class.
        Sets the validator on the `QLineEdit` instances that receive user input
        """

        logger.debug('Initialiazing TimeTrace gui ...')

        self.setupUi(self)
        self.setLayout(self.main_layout)
        self.configure_plots()
        self.set_theme()

        # Sets the icon
        icon = QIcon()
        icon_path = QuDX.get_file_path('icons', 'timetrace.png')
        icon.addFile(icon_path, QSize(), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.run_cps_button.clicked.connect(self.req_start_timetrace)

    def configure_plots(self) -> None:
        """
        Configures the plots in the event of gui initialization

        It sets the label on the plot elements, creates dataline instances for
        the plots and sets any limits, in this case, the temporal axis can´t be
        less than 0
        """
        self.cps_plot.setLabel('left', 'Intensity (cps)')
        self.cps_plot.setLabel('bottom', 'Time (sec)')

        self.cps_dataline = self.cps_plot.plot([], [], pen=QuDX.plot_pens[0])

    @Slot()
    def req_start_timetrace(self) -> None:
        """
        Sends the `start_experiment_signal` to request the start of the
        experiment with the parameters for the acquisition."""

        samp_freq = int(self.samp_freq_spinbox.value())
        refresh_time = float(self.refresh_time_spinbox.value())
        window_time = float(self.window_time_spinbox.value())
        self.start_experiment_signal.emit(samp_freq, refresh_time, window_time)
        self.filename_label.setText('')

    @Slot(np.ndarray, np.ndarray)
    def update_plot(self, time_array: np.ndarray, counts: np.ndarray) -> None:
        """
        Updates the plots when new data is received.

        Parameters
        ----------
        time_array : np.ndarray
            Array containing the x axis values corresponding to time in secs.
        counts : np.ndarray
            Array containing the y axis values corresponding to counts in cps.
        """
        self.cps_dataline.setData(time_array, counts)
        self.cps_label.setText(str(round(counts[-1])))
        self.mean_label.setText(str(round(np.mean(counts))))
        self.std_label.setText(str(round(np.std(counts), 2)))

    @Slot(data_timetrace.TimeTraceData, str)
    def update_on_data_loaded(self, data, filename):

        self.update_plot(data.time_array, data.counts)
        self.filename_label.setText(filename)
        self.cps_plot.setTitle(filename, **{'size': '7pt'})

    def closeEvent(self, event):
        """ Emits the signal to close everything in the closeEvent """
        self.close_experiment_signal.emit()
        super().closeEvent(event)

    def save_plot(self, file_path):
        """
        Saves the current timetrace plot as a png image

        Parameters
        ----------
        file_path : str
            Path to the file to save the image
        """
        exporter = pg.exporters.ImageExporter(self.cps_plot.plotItem)
        exporter.parameters()['width'] = 1000
        exporter.export(file_path)
        logger.debug(f'Exported plot to {file_path}')

if __name__ == '__main__':
    import sys

    app = QApplication()
    form = TimeTraceGui(None)

    form.show()
    sys.exit(app.exec_())
