from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
import sys
import os


class PolarizationMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'polarization.ui'),
            self
        )

        self.init_gui()

    def init_gui(self):

        self.configure_plots()
        self.plot_type_combobox.currentIndexChanged.connect(self.change_plot_type)

    def configure_plots(self):

        self.linear_plot_widget = pg.PlotWidget()
        self.linear_plot_dataline = self.linear_plot_widget.plot([], [], pen='yellow')
        self.plot_layout.addWidget(self.linear_plot_widget)

        r = np.arange(0, 2, 0.01)
        theta = 2 * np.pi * r
        self.polar_plot_figure, self.polar_plot_ax = plt.subplots(subplot_kw={'projection': 'polar'})
        self.polar_plot_canvas = FigureCanvasQTAgg(self.polar_plot_figure)
        
        self.polar_plot_ax.set_facecolor('#000000')
        self.polar_plot_ax.xaxis.label.set_color('#b3aca9')
        self.polar_plot_ax.yaxis.label.set_color('#b3aca9')
        self.polar_plot_figure.set_facecolor('#000000')
        self.polar_plot_ax.tick_params(axis='x', colors='#b3aca9')
        self.polar_plot_ax.spines['polar'].set_color('#b3aca9')


        self.polar_plot_ax.plot(theta, r)
        self.polar_plot_ax.set_rmax(2)
        self.polar_plot_ax.set_rticks([0.5, 1, 1.5, 2])  # Less radial ticks
        self.polar_plot_ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
        self.polar_plot_ax.grid(True)

        self.plot_layout.addWidget(self.polar_plot_canvas)

        self.polar_plot_canvas.hide()

    def change_plot_type(self):

        if self.plot_type_combobox.currentText() == 'Linear':
            self.linear_plot_widget.show()
            self.polar_plot_canvas.hide()
        elif self.plot_type_combobox.currentText() == 'Polar':
            self.linear_plot_widget.hide()
            self.polar_plot_canvas.show()

    @Slot(np.ndarray, np.ndarray)
    def update_plot(self, angles: np.ndarray, fluorescence: np.ndarray) -> None:
        """
        Updates the plots when new data is received.
        """
        self.polar_plot_ax.clear()
        self.polar_plot_ax.plot(np.deg2rad(angles), fluorescence, color='yellow')
        self.polar_plot_canvas.draw()
        self.linear_plot_dataline.setData(angles, fluorescence)
        

if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = PolarizationMainWindow()
    widget.show()
    sys.exit(app.exec_())