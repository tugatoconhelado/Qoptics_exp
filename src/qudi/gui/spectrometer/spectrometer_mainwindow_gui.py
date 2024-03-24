from PySide2.QtWidgets import QDialog, QWidget, QMainWindow
from PySide2.QtCore import Slot, Signal
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg

class SpectrometerMainWindow(QMainWindow):
    """
    Main Window of the spectrometer Experiment
    
    Methods
    -------
    init_gui
    configure_plots
    update_parameter_display
    update_spectrum_plot
    update_status_gui
    update_filter_range
    """
    start_experiment_signal = Signal(int, int, bool, bool, float, bool)
    signal_stop = Signal()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\spectrometer\spectrometer.ui',
            self
        )

        self.current_unit = 'wavelength'
        self.set_parameter_dialog = SpectrometerParametersGui(self)
        self.set_parameters_button.clicked.connect(self.set_parameter_dialog.show)

        self.play_button.clicked.connect(self.start_experiment)
        self.single_spectrum_button.clicked.connect(self.start_experiment)

        self.exit_action.triggered.connect(self.close)

        self.configure_plots()

    def configure_plots(self):
        """
        Setups the axis labels for each PlotWidget and creates their datalines
        """
        self.current_spectrum_plot.setLabel('left', 'Intensity (counts)')
        self.current_spectrum_plot.setLabel('bottom', 'Wavelength (nm)')
        self.average_spectrum_plot.setLabel('left', 'Intensity (counts)')
        self.average_spectrum_plot.setLabel('bottom', 'Wavelength (nm)')
        self.spectrometer_counts_plot.setLabel(
                'left', 'Intensity (kcts)'
                )
        self.spectrometer_counts_plot.setLabel(
                'bottom', 'Time (s)'
                )

        self.current_spectrum_dataline = self.current_spectrum_plot.plot([], [], pen='yellow')
        self.average_spectrum_dataline = self.average_spectrum_plot.plot([], [], pen='yellow')
        self.spectrometer_counts_dataline = self.spectrometer_counts_plot.plot([], [], pen='cyan')
        self.background_spectrum_dataline = self.background_spectrum_plot.plot([], [], pen='yellow')

        self.target_point_current = pg.InfiniteLine(
            pos=600,
            angle=90,
            movable=True,
            pen=pg.mkPen(color='green', width=2)
        )
        self.target_point_average = pg.InfiniteLine(
            pos=600,
            angle=90,
            movable=True,
            pen=pg.mkPen(color='green', width=2)
        )
        self.current_spectrum_plot.addItem(self.target_point_current)
        self.average_spectrum_plot.addItem(self.target_point_average)
        
    @Slot()
    def start_experiment(self):

        button_pressed = self.sender().objectName()
        if button_pressed == 'play_button':
            single_measurement = False
        elif button_pressed == 'single_spectrum_button':
            single_measurement = True
        integration_time, scans_average, electrical_dark, substract_background = self.set_parameter_dialog.get_spectrometer_parameters()
        laser_wavelength = float(self.laser_wavelength_spin_box.value())
        self.start_experiment_signal.emit(
            integration_time, scans_average, electrical_dark, 
            substract_background, laser_wavelength, single_measurement
        )
        self.filename_label.setText('')
        self.current_spectrum_plot.setTitle('')
        self.average_spectrum_plot.setTitle('')

    def get_current_indicator_position_in_wavelength(self, current_unit):

        value = self.target_point_current.value()

        if current_unit == 'energy':
            hc = 1_239.8419 # in eV * nm
            return hc / value
        elif current_unit == 'wavenumber':
            laser_wavenumber = 1e7 / self.laser_wavelength_spin_box.value()
            return 1e7 / (laser_wavenumber - value)
        else:
            return value
        
    def get_average_indicator_position_in_wavelength(self, current_unit):
            
        value = self.target_point_average.value()

        if current_unit == 'energy':
            hc = 1_239.8419 # in eV * nm
            return hc / value
        elif current_unit == 'wavenumber':
            laser_wavenumber = 1e7 / self.laser_wavelength_spin_box.value()
            return 1e7 / (laser_wavenumber - value)
        else:
            return value
            
    def move_current_target_point(self, value):

        self.target_point_current.setPos(value)

    def move_average_target_point(self, value):

        self.target_point_average.setPos(value)
    
    @Slot(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    def update_spectrum_plot(self, x_data: np.ndarray, spectrum: np.ndarray,
            average: np.ndarray, time_array: np.ndarray, total_counts: np.ndarray):
        """ Handles updating the data plots when a data signal is emitted"""

        self.spectrometer_counts_dataline.setData(
            time_array, total_counts / 1000
        )
        self.current_spectrum_dataline.setData(
            x_data, spectrum
        )
        self.average_spectrum_dataline.setData(
            x_data, average
        )

    @Slot(np.ndarray, np.ndarray)
    def update_background_spectrum(self, x_data : np.ndarray, 
        background : np.ndarray) -> None:

        self.background_spectrum_dataline.setData(
            x_data, background
        )

    @Slot(bool)
    def update_status_gui(self, status):

        status_label_dict = {
            True: 'connected',
            False: 'not connected'
        }
        self.connection_status_label.setText(
            f'Status: {status_label_dict[status]}')

class SpectrometerParametersGui(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\spectrometer\set_spectrometer_parameters.ui',
            self
        )

        self.current_values = self.get_spectrometer_parameters()

    def get_spectrometer_parameters(self):

        integration_time = int(self.integration_time_spinbox.value())
        scans_average = int(self.scans_average_spinbox.value())
        electrical_dark = bool(self.electrical_dark_checkbox.checkState())
        substract_background = bool(self.substract_background_checkbox.checkState())
    
        return (integration_time, scans_average, electrical_dark, substract_background)
    
    def accept(self):

        self.current_values = self.get_spectrometer_parameters()
        super().accept()

    def reject(self):

        self._update_values(self.current_values)
        super().reject()

    def _update_values(self, new_values):

        self.integration_time_spinbox.setValue(new_values[0])
        self.scans_average_spinbox.setValue(new_values[1])
        self.electrical_dark_checkbox.setChecked(new_values[2])
        self.substract_background_checkbox.setChecked(new_values[3])

        return new_values

if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = SpectrometerMainWindow()
    widget.show()
    sys.exit(app.exec_())