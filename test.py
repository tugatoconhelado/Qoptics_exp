import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg
import numpy as np


class CustomROI(pg.ROI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_moved_handle = None

    def movePoint(self, handle, pos, modifiers=(), **kwargs):
        self.last_moved_handle = handle
        super().movePoint(handle, pos, modifiers, **kwargs)


class ThinRectSignalEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rectangular Signal with Handle-Specific Behavior")
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.duration = 20
        self.amplitude = 1
        self.snap_step = 2
        self.min_width = 2
        self.x = np.linspace(0, self.duration, 1000)

        self.start = 2
        self.width = 6
        self.height = 0.001

        # Use custom ROI to track handle
        self.roi = CustomROI([self.start, 0.5 - self.height / 2], [self.width, self.height], movable=True, pen='r')
        self.plot_widget.addItem(self.roi)

        # Add scale handles and keep references
        self.left_handle = self.roi.addScaleHandle([0, 0.5], [1, 0.5])   # left
        self.right_handle = self.roi.addScaleHandle([1, 0.5], [0, 0.5])  # right

        self.roi.sigRegionChanged.connect(self.snap_and_update)

        self.rect_curve = self.plot_widget.plot(pen='y')
        self.plot_widget.setYRange(-0.5, 1.5)
        self.plot_widget.setXRange(0, self.duration)

        self.update_plot()

    def rectangular_signal(self, x, start, width, amplitude):
        return np.where((x >= start) & (x <= start + width), amplitude, 0)

    def update_plot(self):
        y = self.rectangular_signal(self.x, self.start, self.width, self.amplitude)
        self.rect_curve.setData(self.x, y)

    def snap_and_update(self):
        pos = self.roi.pos()
        size = self.roi.size()

        moved_handle = self.roi.last_moved_handle

        # Snap values
        snapped_start = round(pos.x() / self.snap_step) * self.snap_step
        snapped_width = round(size.x() / self.snap_step) * self.snap_step

        # Enforce minimum width
        if snapped_width < self.min_width:
            snapped_width = self.min_width

        if snapped_start < 0:
            snapped_start = 0

        # Determine which handle moved
        
        if moved_handle == self.right_handle:

            if snapped_start + snapped_width > self.duration:
                snapped_width = self.duration - snapped_start

                if snapped_width < self.min_width:
                    snapped_width = self.min_width

            self.width = snapped_width

        else:

            if snapped_start + snapped_width > self.duration:
                snapped_start = self.duration - snapped_width
                snapped_width = self.duration - snapped_start
                self.width = snapped_width 
            self.start = snapped_start

        self.roi.blockSignals(True)
        # Reapply clamped & snapped values
        self.roi.setPos([self.start, 0.5 - self.height / 2])
        self.roi.setSize([self.width, self.height])
        self.roi.blockSignals(False)

        self.update_plot()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ThinRectSignalEditor()
    win.resize(800, 400)
    win.show()
    sys.exit(app.exec_())
