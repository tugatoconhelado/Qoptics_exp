from PySide2.QtWidgets import QWidget, QApplication, QDialog
import numpy as np
from PySide2.QtCore import Signal, Slot, QRectF, QSizeF, QPointF, Qt
import pyqtgraph as pg
from qudi.util.uic import loadUi
import functools
import seaborn as sns


class ConfocalWidget(QWidget):

    start_confocal_image_signal = Signal(tuple, tuple, tuple, float)
    stop_confocal_image_signal = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\confocal\confocal_scan.ui',
            self
        )
        self.configure_plots()

        self.scan_parameters_dialog = ScanParametersDialog(self)
        self.scan_parameters_dialog.init_gui()
        
        self.set_scan_button.clicked.connect(
            self.scan_parameters_dialog.show, Qt.QueuedConnection)

        self.image_button.clicked.connect(
            self.req_scan, Qt.QueuedConnection)
        self.stop_button.clicked.connect(
            self.on_stop_image, Qt.QueuedConnection)
        

    def configure_plots(self):

        self.image_fw_widget = HeatmapWidget()
        self.img_fw_layout.addWidget(self.image_fw_widget)

        self.image_bw_widget = HeatmapWidget()
        self.img_bw_layout.addWidget(self.image_bw_widget)

        self.image_fw_widget.heatmap.setLabel('left', 'Slow axis (μm)')
        self.image_bw_widget.heatmap.setLabel('left', 'Slow axis (μm)')
        self.image_fw_widget.heatmap.setLabel('bottom', 'Fast axis (μm)')
        self.image_bw_widget.heatmap.setLabel('bottom', 'Fast axis (μm)')
        self.image_fw_widget.colorbar.setLabel('top', 'Intensity<br>(kcts / sec)')
        self.image_bw_widget.colorbar.setLabel('top', 'Intensity<br>(kcts / sec)')
        self.image_fw_widget.heatmap.setTitle('Forward scan', **{'size': '7pt'})
        self.image_bw_widget.heatmap.setTitle('Backward scan', **{'size': '7pt'})

    @Slot()
    def req_scan(self):
        """
        Emits the `start_confocal_image_signal` to request measurement.
        """
        scan_size, offset, pixels, pixel_time = self.scan_parameters_dialog.get_scan_parameters()
        self.start_confocal_image_signal.emit(
            scan_size, offset, pixels, pixel_time
        )
        self.filename_label.setText('')
        self.image_fw_widget.heatmap.setTitle('Forward scan', **{'size': '7pt'})

    def on_stop_image(self):

        #self.statusbar.showMessage('Stopping confocal image acquisition')
        #self.statusbar.removeWidget(self.image_progress_bar)
        self.stop_confocal_image_signal.emit()

    @Slot(np.ndarray, np.ndarray, float)
    def update_image(self, img_fw, img_bw, progress=0.0):

        self.image_fw_widget.update_img(img_fw)
        self.image_bw_widget.update_img(img_bw)

    @Slot(tuple, tuple, tuple)
    def configure_image_axis(self, scan_size, offset, pixels):
        
        self.image_fw_widget.set_image_size(scan_size, offset, pixels)
        self.image_bw_widget.set_image_size(scan_size, offset, pixels)

    def on_position_changed(self, new_position):

        self.image_fw_widget.move_pos_indicator(new_position)
        self.image_bw_widget.move_pos_indicator(new_position)


class ScanParametersDialog(QDialog):

    status_msg = Signal(str)

    def __init__(self, parent = None):
        super().__init__(parent=parent)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\confocal\set_scan_parameters.ui',
            self
        )
        self.init_gui()

    def init_gui(self) -> None:

        # When clicking the buttons sets the variable
        self.scan_size_5_button.clicked.connect(
            functools.partial(self._change_scan_size_spinbox, 5)
        )
        self.scan_size_10_button.clicked.connect(
            functools.partial(self._change_scan_size_spinbox, 10)
        )
        self.scan_size_20_button.clicked.connect(
            functools.partial(self._change_scan_size_spinbox, 20)
        )
        self.scan_size_40_button.clicked.connect(
            functools.partial(self._change_scan_size_spinbox, 40)
        )
        self.scan_size_80_button.clicked.connect(
            functools.partial(self._change_scan_size_spinbox, 80)
        )
        self.scan_pixel_16_button.clicked.connect(
            functools.partial(self._change_scan_pixel_spinbox, 16)
        )
        self.scan_pixel_32_button.clicked.connect(
            functools.partial(self._change_scan_pixel_spinbox, 32)
        )
        self.scan_pixel_64_button.clicked.connect(
            functools.partial(self._change_scan_pixel_spinbox, 64)
        )
        self.scan_pixel_128_button.clicked.connect(
            functools.partial(self._change_scan_pixel_spinbox, 128)
        )
        self.scan_pixel_256_button.clicked.connect(
            functools.partial(self._change_scan_pixel_spinbox, 256)
        )

        self.scan_pixel_32_button.clicked.emit()
        self.scan_size_5_button.clicked.emit()
        self.pixel_time_spinbox.setValue(5)
        self.slow_axis_offset_spinbox.setValue(0)
        self.fast_axis_offset_spinbox.setValue(0)

        self.current_values = self.get_scan_parameters()

    def accept(self):

        self.current_values = self.get_scan_parameters()
        self.status_msg.emit(f'Accepted new scan parameters {self.current_values}')
        super().accept()

    def reject(self):

        self._update_values(self.current_values)
        super().reject()

    def _update_values(self, new_values):

        self.fast_axis_scan_size_spinbox.setValue(new_values[0][0])
        self.fast_axis_offset_spinbox.setValue(new_values[1][0])
        self.fast_axis_pixels_spinbox.setValue(new_values[2][0])
        
        self.slow_axis_scan_size_spinbox.setValue(new_values[0][1])
        self.slow_axis_offset_spinbox.setValue(new_values[1][1])
        self.slow_axis_pixels_spinbox.setValue(new_values[2][1])

        self.pixel_time_spinbox.setValue(new_values[3])

        return new_values

    def get_scan_parameters(self):

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

        return (scan_size, offset, pixels, pixel_time)

    def _change_scan_size_spinbox(self, value):
        self.fast_axis_scan_size_spinbox.setValue(float(value))
        self.slow_axis_scan_size_spinbox.setValue(float(value))

    def _change_scan_pixel_spinbox(self, value):
        self.fast_axis_pixels_spinbox.setValue(int(value))
        self.slow_axis_pixels_spinbox.setValue(int(value))

    @Slot(tuple)
    def set_offset(self, new_offset):

        self.fast_axis_offset_spinbox.setValue(float(new_offset[0]))
        self.slow_axis_offset_spinbox.setValue(float(new_offset[1]))

        self.current_values = self.get_scan_parameters()


class HeatmapWidget(pg.GraphicsLayoutWidget):

    xy_pos_signal = Signal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.selected_point = None

        self.heatmap = self.addPlot(0, 0)
        self.heatmap.getViewBox().setAspectLocked(True)

        #self.rect = QRectF(QPointF(0.0, 0.0), QSizeF(10.0, -10.0))
        self.rect = QRectF(0, 0, 1, 1)

        self.image_item = pg.ImageItem(axisOrder='row-major')
        self.image_item.setImage(np.zeros((10, 10)))
        self.image_item.setRect(self.rect)
        self.heatmap.addItem(self.image_item)
        self.colorbar = self.heatmap.addColorBar(
            self.image_item, colorMap=pg.colormap.getFromMatplotlib('rocket'),
            *args, **kwargs
        )
        #self.colorbar = self.heatmap.addColorBar(self.image_item, colorMap=pg.colormap.getFromColorcet('rainbow4'))

        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r'))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('r'))
        self.heatmap.addItem(self.v_line, ignoreBounds=True)
        self.heatmap.addItem(self.h_line, ignoreBounds=True)

        self.scene().sigMouseClicked.connect(self.mouse_pressed)
        self.create_menu()
        self.mouse_enabled = False

    def mouse_pressed(self, event):
        if self.mouse_enabled:
            pos = event.scenePos()
            mapped_pos = self.image_item.getViewBox().mapSceneToView(pos)
            x = float(mapped_pos.x())
            y = float(mapped_pos.y())
            self.selected_point = (x, y)
            self.move_pos_indicator(self.selected_point)
            self.heatmap.update()
            self.xy_pos_signal.emit(self.selected_point)

    def set_image_size(self, scan_size: tuple, offset: tuple, pixels: tuple):

        self.rect.setSize(QSizeF(scan_size[0], -scan_size[1]))
        self.rect.moveCenter(QPointF(offset[0], offset[1]))
        self.v_line.setPos(offset[0])
        self.h_line.setPos(offset[1])
        self.image_item.setRect(self.rect)

    def update_img(self, img):

        img = np.array(img)
        self.image_item.setImage(np.flip(img, 0))
        self.colorbar.setLevels((np.min(img), np.max(img)))

    @Slot(tuple)
    def move_pos_indicator(self, new_pos: tuple):

        self.v_line.setPos(new_pos[0])
        self.h_line.setPos(new_pos[1])

    def create_menu(self):

        self.test_action = self.heatmap.vb.menu.addAction('Set (X, Y) point with cursor')
        self.test_action.setCheckable(True)
        self.test_action.toggled.connect(self.enable_set_point)

    def enable_set_point(self):

        self.mouse_enabled = not self.mouse_enabled
        if self.mouse_enabled:
            cursor = Qt.CrossCursor
            self.setCursor(cursor)
        elif not self.mouse_enabled:
            cursor = Qt.ArrowCursor
            self.setCursor(cursor)

if __name__ == '__main__':

    import sys
    sys.path.append('artwork')
    app = QApplication(sys.argv)
    w = ConfocalWidget()
    w.show()
    sys.exit(app.exec_())