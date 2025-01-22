from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.confocal.confocal_widget import HeatmapWidget
import numpy as np
import pyqtgraph as pg
import os


class TrackingWidget(QWidget):

    max_z_signal = Signal(tuple, tuple, tuple, float, bool)
    max_xy_signal = Signal(tuple, tuple, tuple, float, bool)
    max_xyz_signal = Signal(tuple, tuple)
    maxing_signal = Signal()                                            
    track_signal = Signal(tuple, tuple, tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            os.path.join(os.path.dirname(__file__), 'tracking.ui'),
            self
        )

        self.tracking_parameters_dialog = TrackingParametersDialog(self)
        self.set_tracking_parameters_button.clicked.connect(self.tracking_parameters_dialog.show)

        self.max_z_button.clicked.connect(self.handle_max_z)
        self.max_xy_button.clicked.connect(self.handle_max_xy)
        self.max_xyz_button.clicked.connect(self.handle_max_xyz)
        self.track_button.clicked.connect(self.handle_track)

        self.configure_plots()

    def handle_max_z(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        self.maxing_signal.emit()
        self.max_z_signal.emit(*parameters[1])

    def handle_max_xy(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        print(parameters[0])
        self.maxing_signal.emit()
        self.max_xy_signal.emit(*parameters[0])

    def handle_max_xyz(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        self.maxing_signal.emit()
        self.max_xyz_signal.emit(parameters[0], parameters[1])

    def handle_track(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        self.maxing_signal.emit()
        self.track_signal.emit(
            parameters[0], parameters[1], parameters[2])

    def configure_plots(self):

        self.fast_scan_plot.setLabel('bottom', 'Fast Axis (μm)')
        self.fast_scan_plot.setLabel('left', 'Intensity (kcts)')
        self.slow_scan_plot.setLabel('bottom', 'Slow Axis (μm)')
        self.slow_scan_plot.setLabel('left', 'Intensity (kcts)')

        self.z_scan_plot.setLabel('left', 'Intensity (kcts)')
        self.z_scan_plot.setLabel('bottom', 'z (μm)')

        self.tracking_points_plot.setLabel('left', 'Fast Axis (μm)')
        self.tracking_points_plot.setLabel('bottom', 'Slow Axis (μm)')

        self.xy_scan_widget = HeatmapWidget(width=12.5)
        self.xy_scan_layout.insertWidget(0, self.xy_scan_widget)

        self.xy_scan_layout.setStretch(0, 1.6)
        self.xy_scan_layout.setStretch(1, 1)

        self.xy_scan_widget.heatmap.setLabel('bottom', 'Fast Axis (μm)')
        self.xy_scan_widget.heatmap.setLabel('left', 'Slow Axis (μm)')

        self.fast_scan_profile_dataline = self.fast_scan_plot.plot([], [], pen=None, symbol='o',
              symbolPen=pg.mkPen(color='blue', width=0),                                      
              symbolBrush=pg.mkBrush('blue'),
              symbolSize=7)
        self.fast_scan_profile_fit_dataline = self.fast_scan_plot.plot(
            [], [], pen='yellow'
        )

        self.slow_scan_profile_dataline = self.slow_scan_plot.plot([], [], pen=None, symbol='o',
              symbolPen=pg.mkPen(color='blue', width=0),                                      
              symbolBrush=pg.mkBrush('blue'),
              symbolSize=7)
        self.slow_scan_profile_fit_dataline = self.slow_scan_plot.plot(
            [], [], pen='yellow'
        )

        self.z_scan_dataline = self.z_scan_plot.plot([], [],
            pen=None, symbol='o',
            symbolPen=pg.mkPen(color='blue', width=0),                                      
            symbolBrush=pg.mkBrush('blue'),
            symbolSize=7
        )
        self.z_scan_fit_dataline = self.z_scan_plot.plot(
            [], [], pen='yellow'
        )
        
        self.tracking_points_dataline = self.tracking_points_plot.plot([], [],
            pen=None, symbol='o',
            symbolPen=pg.mkPen(color='cyan', width=0),                                      
            symbolBrush=pg.mkBrush('cyan'),
            symbolSize=7
        )

    @Slot(np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    def plot_point_profile(self, fast_axis: np.ndarray, fast_prof: np.ndarray,
            slow_axis: np.ndarray, slow_prof: np.ndarray) -> None:
        """
        Plot the fast and slow axis profiles for a given point.
        
        Parameters
        ----------
        fast_axis : np.ndarray
            Fast axis positions.
        fast_prof : np.ndarray
            Fast axis profile.
        slow_axis : np.ndarray
            Slow axis positions.
        slow_prof : np.ndarray
            Slow axis profile.
        """
        self.fast_scan_profile_dataline.setData(
            fast_axis, fast_prof)
        self.slow_scan_profile_dataline.setData(
            slow_axis, slow_prof)
        self.fast_scan_profile_fit_dataline.setData([], [])
        self.slow_scan_profile_fit_dataline.setData([], [])

    @Slot(tuple, tuple)
    def plot_point_fit(self, fast_fit_prof: tuple, slow_fit_prof: tuple):
        """
        Plot the fast and slow axis profiles for a given point.
        
        Parameters
        ----------
        fast_fit_prof : tuple
            Tuple containing the fast axis and fit.
        slow_fit_prof : tuple
            Tuple containing the slow axis and fit.
        """
        #self.xy_scan_widget.move_pos_indicator(point)

        self.fast_scan_profile_fit_dataline.setData(
            fast_fit_prof[0], fast_fit_prof[1])
        self.slow_scan_profile_fit_dataline.setData(
            slow_fit_prof[0], slow_fit_prof[1])

    @Slot(np.ndarray)
    def plot_tracking_points(self, points: np.ndarray) -> None:
        """
        Plot the tracking points.
        
        Parameters
        ----------
        points : np.ndarray
            Array containing the tracking points.
        """
        self.tracking_points_dataline.setData(points[:, 0], points[:, 1])

    @Slot(np.ndarray)
    def update_image(self, img_fw: np.ndarray) -> None:

        self.xy_scan_widget.update_img(img_fw)

    @Slot(tuple, tuple, tuple)
    def set_image_size(self, scan_size: tuple, offset: tuple, pixels: tuple):

        self.update_image(
            np.zeros((pixels[0], pixels[1]))
        )
        self.xy_scan_widget.set_image_size(scan_size, offset, pixels)

    @Slot(np.ndarray, np.ndarray)
    def plot_z_profile(self, z_data: np.ndarray, z_prof: np.ndarray) -> None:
        """
        Plot the z scan profile.
        
        Parameters
        ----------
        z_data : np.ndarray
            Tuple containing the z scan data.
        z_prof : np.ndarray
            Tuple containing the z scan profile.
        """
        self.z_scan_dataline.setData(z_data, z_prof)
        self.z_scan_fit_dataline.setData([], [])

    @Slot(tuple)
    def plot_z_fit(self, z_fit_prof: tuple):
        """
        Plot the z scan profile and fit.
        
        Parameters
        ----------
        z_data : tuple
            Tuple containing the z scan data.
        z_prof : tuple
            Tuple containing the z scan profile and fit.
        """
        self.z_scan_fit_dataline.setData(z_fit_prof[0], z_fit_prof[1])


class TrackingParametersDialog(QDialog):

    status_msg = Signal(str)
    tracking_monitor_signal = Signal(str)
    connect_tracking_interval_signal = Signal(bool)
    set_tracking_parameters_signal = Signal(tuple, tuple, tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\confocal\set_tracking_parameters.ui',
            self
        )
        self.init_gui()

        self.current_values = self.get_parameters()

    def init_gui(self):
            
        self.current_values = self.get_parameters()

    def accept(self):

        self.current_values = self.get_parameters()
        self.status_msg.emit(f'Accepted new scan parameters {self.current_values}')
        self.set_tracking_parameters_signal.emit(*self.current_values)

        if self.track_with_tcspc_radiobutton.isChecked():
            self.tracking_monitor_signal.emit('TCSPC')
        elif self.track_with_timetrace_radiobutton.isChecked():
            self.tracking_monitor_signal.emit('TimeTrace')

        if self.connect_interval_track_to_tcspc_checkbox.isChecked():
            self.connect_tracking_interval_signal.emit(True)
        else:
            self.connect_tracking_interval_signal.emit(False)
        super().accept()

    def reject(self):

        self._update_values(self.current_values)
        super().reject()

    def _update_values(self, new_values):

        xy_scan_parameters = new_values[0]
        self.fast_axis_scan_size_spinbox.setValue(xy_scan_parameters[0][0])
        self.fast_axis_offset_spinbox.setValue(xy_scan_parameters[1][0])
        self.fast_axis_pixels_spinbox.setValue(xy_scan_parameters[2][0])
        
        self.slow_axis_scan_size_spinbox.setValue(xy_scan_parameters[0][1])
        self.slow_axis_offset_spinbox.setValue(xy_scan_parameters[1][1])
        self.slow_axis_pixels_spinbox.setValue(xy_scan_parameters[2][1])

        self.pixel_time_spinbox.setValue(xy_scan_parameters[3])
        self.xy_fit_gauss_checkbox.setChecked(xy_scan_parameters[4])

        z_scan_parameters = new_values[1]

        self.z_scan_size_spinbox.setValue(z_scan_parameters[0][0])
        self.z_offset_spinbox.setValue(z_scan_parameters[1][0])
        self.z_pixels_spinbox.setValue(z_scan_parameters[2][0])
        self.z_pixel_time_spinbox.setValue(z_scan_parameters[3])
        self.z_fit_gauss_checkbox.setChecked(z_scan_parameters[4])

        tracking_parameters = new_values[2]

        self.track_interval_radiobutton.setChecked(tracking_parameters[0][0])
        self.track_intensity_radiobutton.setChecked(tracking_parameters[1][0])
        self.track_intensity_spinbox.setValue(tracking_parameters[1][1])
        self.track_interval_spinbox.setValue(tracking_parameters[0][1])

        return new_values

    def get_parameters(self):

        scan_size = (
            self.fast_axis_scan_size_spinbox.value(),
            self.slow_axis_scan_size_spinbox.value()
        )
        offset = (
            self.fast_axis_offset_spinbox.value(),
            self.slow_axis_offset_spinbox.value()
        )
        pixels = (
            self.fast_axis_pixels_spinbox.value(),
            self.slow_axis_pixels_spinbox.value()
        )
        pixel_time = self.pixel_time_spinbox.value()
        fit_gauss = self.xy_fit_gauss_checkbox.isChecked()
        xy_scan_parameters = (scan_size, offset, pixels, pixel_time, fit_gauss)

        z_scan_size = self.z_scan_size_spinbox.value()
        z_offset = self.z_offset_spinbox.value()
        z_pixels = self.z_pixels_spinbox.value()
        pixel_time = self.z_pixel_time_spinbox.value()
        fit_gauss = self.z_fit_gauss_checkbox.isChecked()

        z_scan_parameters = ((z_scan_size, ), (z_offset, ), (z_pixels, ), pixel_time, fit_gauss)

        track_interval = bool(self.track_interval_radiobutton.isChecked())
        track_intensity = bool(self.track_intensity_radiobutton.isChecked())

        track_interval_duration = self.track_interval_spinbox.value()
        track_intensity_value = self.track_intensity_spinbox.value()

        tracking_parameters = (
            (track_intensity, track_intensity_value),
            (track_interval, track_interval_duration)
        )

        return (xy_scan_parameters, z_scan_parameters, tracking_parameters)
    
    @Slot(tuple)
    def set_offset(self, offset: tuple) -> None:

        self.fast_axis_offset_spinbox.setValue(offset[0])
        self.slow_axis_offset_spinbox.setValue(offset[1])

        self.accept()

    @Slot(float)
    def set_z_offset(self, offset: tuple) -> None:

        self.z_offset_spinbox.setValue(offset[0])

if __name__ == '__main__':
    import sys
    sys.path.append('artwork')

    app = QApplication(sys.argv)
    widget = TrackingWidget()
    widget.show()
    sys.exit(app.exec_())