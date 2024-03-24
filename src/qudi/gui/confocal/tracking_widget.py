from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
from qudi.gui.confocal.confocal_widget import HeatmapWidget
import numpy as np
import pyqtgraph as pg


class TrackingWidget(QWidget):

    max_z_signal = Signal(tuple, tuple, tuple, float)
    max_xy_signal = Signal(tuple, tuple, tuple, float)
    max_xyz_signal = Signal(tuple, tuple, tuple, float, tuple, tuple, tuple, float)
    track_signal = Signal(tuple, bool, int, bool, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\confocal\tracking.ui',
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
        self.max_z_signal.emit(*parameters[1])

    def handle_max_xy(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        print(parameters[0])
        self.max_xy_signal.emit(*parameters[0])

    def handle_max_xyz(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        self.max_xyz_signal.emit(*parameters[0], *parameters[1])

    def handle_track(self):

        parameters = self.tracking_parameters_dialog.get_parameters()
        self.track_signal.emit(
            *parameters[0], *parameters[1], *parameters[2])

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
              symbolBrush=pg.mkBrush(0, 0, 255, 255),
              symbolSize=7)
        self.fast_scan_profile_fit_dataline = self.fast_scan_plot.plot(
            [], [], pen='red'
        )

        self.slow_scan_profile_dataline = self.slow_scan_plot.plot([], [], pen=None, symbol='o',
              symbolPen=pg.mkPen(color='blue', width=0),                                      
              symbolBrush=pg.mkBrush(0, 0, 255, 255),
              symbolSize=7)
        self.slow_scan_profile_fit_dataline = self.slow_scan_plot.plot(
            [], [], pen='red'
        )

        self.z_scan_dataline = self.z_scan_plot.plot([], [],
            pen=None, symbol='o',
            symbolPen=pg.mkPen(color='blue', width=0),                                      
            symbolBrush=pg.mkBrush(0, 0, 255, 255),
            symbolSize=7
        )
        self.z_scan_fit_dataline = self.z_scan_plot.plot(
            [], [], pen='red'
        )
        
        self.tracking_points_dataline = self.tracking_points_plot.plot([], [],
            pen=None, symbol='o',
            symbolPen=pg.mkPen(color='blue', width=0),                                      
            symbolBrush=pg.mkBrush(0, 0, 255, 255),
            symbolSize=7
        )

    def plot_point_fit(self, point, fast_prof: tuple, slow_prof: tuple):
        """
        Plot the fast and slow axis profiles for a given point.
        
        Parameters
        ----------
        point : tuple
            Tuple containing the fast and slow axis positions.
        fast_prof : tuple
            Tuple containing the fast axis profile and fit.
        slow_prof : tuple
            Tuple containing the slow axis profile and fit.
        """
        self.xy_scan_widget.move_pos_indicator(point)

        # Plot fast axis profiles
        self.fast_scan_profile_dataline.setData(
            fast_prof[0][0], fast_prof[0][1])
        self.fast_scan_profile_fit_dataline.setData(
            fast_prof[1][0], fast_prof[1][1])

        # Plot slow axis profiles
        self.slow_scan_profile_dataline.setData(
            slow_prof[0][0], slow_prof[0][1])
        self.slow_scan_profile_fit_dataline.setData(
            slow_prof[1][0], slow_prof[1][1], pen='red', symbol=None)

    @Slot(np.ndarray)
    def update_image(self, img_fw: np.ndarray) -> None:

        self.xy_scan_widget.update_img(img_fw)

    @Slot(tuple, tuple, tuple)
    def set_image_sige(self, scan_size: tuple, offset: tuple, pixels: tuple):

        self.xy_scan_widget.set_image_size(scan_size, offset, pixels)

    @Slot(tuple, tuple)
    def plot_z_fit(self, z_data: tuple, z_prof: tuple):
        """
        Plot the z scan profile and fit.
        
        Parameters
        ----------
        z_data : tuple
            Tuple containing the z scan data.
        z_prof : tuple
            Tuple containing the z scan profile and fit.
        """
        self.z_scan_dataline.setData(z_data[0], z_data[1])
        self.z_scan_fit_dataline.setData(z_prof[0], z_prof[1])


class TrackingParametersDialog(QDialog):

    status_msg = Signal(str)

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

        z_scan_parameters = new_values[1]

        self.z_scan_size_spinbox.setValue(z_scan_parameters[0][0])
        self.z_offset_spinbox.setValue(z_scan_parameters[1][0])
        self.z_pixels_spinbox.setValue(z_scan_parameters[2][0])

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
        pixel_time = 5 # In ms
        xy_scan_parameters = (scan_size, offset, pixels, pixel_time)

        z_scan_size = self.z_scan_size_spinbox.value()
        z_offset = self.z_offset_spinbox.value()
        z_pixels = self.z_pixels_spinbox.value()

        z_scan_parameters = ((z_scan_size, ), (z_offset, ), (z_pixels, ), pixel_time)

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

        self.current_values = self.get_parameters()

    @Slot(float)
    def set_z_offset(self, offset: tuple) -> None:

        self.z_offset_spinbox.setValue(offset)

if __name__ == '__main__':
    import sys
    sys.path.append('artwork')

    app = QApplication(sys.argv)
    widget = TrackingWidget()
    widget.show()
    sys.exit(app.exec_())