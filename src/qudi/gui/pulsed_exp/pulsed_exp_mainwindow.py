from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QTableWidgetItem, QFileDialog
from PySide2.QtCore import Slot, Signal, QDir, QObject
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os
from pathlib import Path
from qudi.gui.pulsed_exp.sequence_editor.editor import SequenceEditor


class PulsedExpMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    pb_output_status_signal = Signal(tuple)
    pb_output_stop_signal = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.join(os.path.dirname(__file__), "pulsed_experiments.ui"), self)

        self.sequence_editor = SequenceEditor()

        self.sequence_editor.seq_name_sig.connect(self.update_sequence_name_display)
        self.sequence_editor.sequence_changed.connect(self.update_x_axis_options)

        self.stop_output_button.clicked.connect(self.pb_output_stop_signal.emit)
        self.run_output_button.clicked.connect(self._get_output_state)

        self.edit_sequence_btn.clicked.connect(self.show_sequence_editor)
        self.configure_plots()

    @property
    def sequence(self):
        return self.sequence_editor.sequence

    def configure_plots(self):

        self.pulsed_exp_dataline = self.pulsed_exp_plot.plot([], pen='yellow')
        self.pulsed_exp_plot.setLabel('left', 'Counts')

        self.errorbars = pg.ErrorBarItem(pen=(31, 119, 180), beam=0.3)
        self.pulsed_exp_plot.addItem(self.errorbars)

    @Slot()
    def show_sequence_editor(self):
        self.sequence_editor.show()

    @Slot(str)
    def update_status_bar(self, msg: str):
        self.statusbar.showMessage(msg)

    @Slot(str)
    def update_sequence_name_display(self, name):
        self.sequence_name_label.setText(f"Sequence: {name}")

    @Slot()
    def update_x_axis_options(self):
        self.x_axis_param_combo.clear()

        self.x_axis_param_combo.addItem("Iteration Number (i)")
        for ch_name, channel in self.sequence_editor.sequence.channels.items():
            sorted_pulses = sorted(channel.pulses, key=lambda p: p.start)
            for idx, pulse in enumerate(sorted_pulses, start=1):

                if not pulse.start_sweep and not pulse.duration_sweep:
                    continue

                name = f"{channel.name} - Pulse {idx}"
                if pulse.comment:
                    name += f" ({pulse.comment})"

                self.x_axis_param_combo.addItem(name, pulse.uid)

    def generate_x_axis(self, num_iterations):

        param_type = self.x_axis_param_combo.currentText()
        if param_type == "Iteration Number (i)":
            return np.arange(num_iterations)

        selected_pulse_uid = self.x_axis_param_combo.currentData()
        x_values = []
        pulse = self.sequence.get_pulse(selected_pulse_uid)

        if pulse.start_sweep:
            iterations = np.linspace(0, num_iterations, num_iterations)
            start = pulse.start
            env = {"i": iterations, "np": np, "S": start}
            x_values = eval(pulse.start_sweep,{"__builtins__": None}, env)
            return x_values
        elif pulse.duration_sweep:
            iterations = np.linspace(0, num_iterations, num_iterations)
            width = pulse.duration
            env = {"i": iterations, "np": np, "W": width}
            x_values = eval(pulse.duration_sweep,{"__builtins__": None}, env)
            return x_values

    @Slot(np.ndarray, np.ndarray, np.ndarray)
    def update_pulsed_exp_plot(self, x: np.ndarray, y: np.ndarray, st_dev: np.ndarray):
        """
        Update the pulsed experiment plot with new data.
        """
        y = y.flatten()
        x = self.generate_x_axis(len(y))
        self.pulsed_exp_dataline.setData(x, y)
        self.errorbars.setData(x=x, y=y, height=2 * st_dev)
        self.pulsed_exp_plot.setYRange(min(y), max(y))

        
    @Slot()
    def _get_output_state(self):
        """
        This function is called when the user clicks the "Run" button.
        It gets the state of the PB outputs checkboxes and sends the
        signal to the logic to turn on/off the outputs.
        """
        status = (
            int(self.pb0_checkbox.isChecked()),
            int(self.pb1_checkbox.isChecked()),
            int(self.pb2_checkbox.isChecked()),
            int(self.pb3_checkbox.isChecked()),
            int(self.pb4_checkbox.isChecked()),
            int(self.pb5_checkbox.isChecked()),
        )
        self.pb_output_status_signal.emit(status)
        return status

    @Slot(str)
    def update_filename(self, filepath: str):
        path = Path(filepath)
        filename = path.name
        self.filename_label.setText(filename)

if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication
    print(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    import artwork.qudi_icons_rc

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = PulsedExpMainWindow()
    widget.show()
    sys.exit(app.exec_())
