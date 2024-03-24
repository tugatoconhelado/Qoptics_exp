from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys


class PositionControlWidget(QWidget):

    position_changed = Signal(tuple)
    z_changed = Signal(float)
    set_offset_signal = Signal(tuple)
    status_msg = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(
            r'C:\EXP\python\Qoptics_exp\src\qudi\gui\confocal\position_control.ui',
            self
        )

        self.scrollbar_um = 200  # for the scrollbar only
        self.scrollbar_steps = 20000  # Number of steps for scrollbar
        self.slider_dragging = False
        self.xy_pos = (0, 0)
        self.z_pos = 0

        self.init_gui()

    def init_gui(self):
        """
        Initialise the GUI.
        """
        self.z_scrollbar.valueChanged.connect(self._on_z_scrollbar_value_changed)
        self.z_scrollbar.setRange(0, self.scrollbar_steps)
        self.z_scrollbar.setValue(int(self.scrollbar_steps / 2))
        self.z_scrollbar.sliderPressed.connect(self._on_z_scrollbar_slider_pressed)
        self.z_scrollbar.sliderReleased.connect(self._on_z_scrollbar_slider_released)

        self.z_step_spinbox.valueChanged.connect(self._on_z_step_changed)
        self.z_step_spinbox.valueChanged.emit(self.z_step_spinbox.value())
        self.z_position_spinbox.editingFinished.connect(self._on_z_value_changed)

        self.left_button.clicked.connect(lambda: self._on_move_xy((-1, 0)))
        self.right_button.clicked.connect(lambda: self._on_move_xy((1, 0)))
        self.up_button.clicked.connect(lambda: self._on_move_xy((0, 1)))
        self.down_button.clicked.connect(lambda: self._on_move_xy((0, -1)))

        self.x_position_spinbox.editingFinished.connect(self._on_xy_position_changed)
        self.y_position_spinbox.editingFinished.connect(self._on_xy_position_changed)

        self.set_offset_button.clicked.connect(self._on_set_offset_button_pressed)

    def _on_set_offset_button_pressed(self):
        """
        Emit the offset signal when the set offset button is pressed.
        """
        self.set_offset_signal.emit(
            (round(self.x_position_spinbox.value(), 2),
             round(self.y_position_spinbox.value(), 2))
        )
        self.status_msg.emit("Offset set to (%.2f, %.2f)" % (
            round(self.x_position_spinbox.value(), 2),
            round(self.y_position_spinbox.value(), 2)
        ))

    def _on_z_scrollbar_slider_pressed(self):
        """
        Just handle the slider pressed event.
        """
        self.slider_dragging = True

    def _on_z_scrollbar_slider_released(self):
        """
        Handle the slider released event
        """
        self.slider_dragging = False
        self.z_scrollbar.valueChanged.emit(self.z_scrollbar.value())

    def _on_z_step_changed(self, new_z_step):
        """
        Handle the z step changed event. 

        The z step is in microns, but the scrollbar is in steps.
        """
        new_step = round(new_z_step, 2)
        new_step = new_step * (self.scrollbar_steps) / self.scrollbar_um
        self.z_scrollbar.setSingleStep(new_step)
        self.z_scrollbar.setPageStep(new_step)

    def _on_z_scrollbar_value_changed(self, new_step_value):
        """
        Handle the z scrollbar value changed event.

        The z scrollbar is in steps, but the z position is in microns.
        """
        # To microns
        new_z = (abs(new_step_value - self.scrollbar_steps)*
            self.scrollbar_um /
            self.scrollbar_steps
        )
        new_z = round(new_z, 2)
        self.z_position_spinbox.setValue(new_z)
        if self.slider_dragging is not True:
            self.go_to_z_point(new_z)

    def _on_z_value_changed(self):
        """
        Handle the z value changed event when editing the spinbox.
        """
        new_z = round(self.z_position_spinbox.value(), 2)
        new_z_steps = int(abs(new_z) * self.scrollbar_steps / self.scrollbar_um)
        self.z_scrollbar.setValue(abs(new_z_steps - self.scrollbar_steps))

    @Slot(tuple)
    def _on_move_xy(self, direction: tuple) -> None:
        """
        Handle the move xy event when pressing position buttons.
        """
        current_pos = (
            round(self.x_position_spinbox.value(), 2),
            round(self.y_position_spinbox.value(), 2)
        )
        step = round(self.xy_step_spinbox.value(), 2)
        new_pos = (
            round(current_pos[0] + direction[0] * step, 2),
            round(current_pos[1] + direction[1] * step, 2)
        )
        self.set_xy_point(new_pos)

    def _on_xy_position_changed(self):
        """
        Handle the xy position changed event when editing the spinboxes.
        """
        new_x = round(self.x_position_spinbox.value(), 2)
        new_y = round(self.y_position_spinbox.value(), 2)
        self.set_xy_point((new_x, new_y))

    def set_xy_point(self, point):
        """
        Set the xy point and emit the position changed signal.
        """
        self.xy_pos = point
        self.x_position_spinbox.setValue(round(point[0], 2))
        self.y_position_spinbox.setValue(round(point[1], 2))
        self.go_to_xy_point(point)

    @Slot(tuple)
    def set_z_point(self, point : tuple):

        self.z_pos = point
        self.z_position_spinbox.setValue(round(point[0], 2))
        self.go_to_z_point(point[0])

    def go_to_xy_point(self, new_point):
        """
        Emit the position changed signal.

        This signal is intended to be connected to the backend of confocal.
        """
        self.position_changed.emit(new_point)

    def go_to_z_point(self, new_point):
        """
        Emit the z changed signal.

        This signal is intended to be connected to the backend of confocal.
        """
        self.z_changed.emit(float(new_point))


if __name__ == '__main__':
    import sys
    sys.path.append('artwork')

    app = QApplication(sys.argv)
    widget = PositionControlWidget()
    widget.show()
    sys.exit(app.exec_())