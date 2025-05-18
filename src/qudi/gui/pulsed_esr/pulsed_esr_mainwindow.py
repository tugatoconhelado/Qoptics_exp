from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication
from PySide2.QtCore import Slot, Signal, QDir, QObject
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class PulsedESRMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    pb_output_status_signal = Signal(tuple)
    pb_output_stop_signal = Signal()
    clear_channels_signal = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.join(os.path.dirname(__file__), "pulsed_esr2.ui"), self)

        self.iteration_start_spinbox.valueChanged.connect(self._set_max_iteration_end)
        self.stop_output_button.clicked.connect(self.pb_output_stop_signal.emit)
        self.run_output_button.clicked.connect(self._get_output_state)
        self.clear_channels_button.clicked.connect(self._clear_gui)

    @Slot()
    def _clear_gui(self):

        self.channels_tablewidget.clearContents()
        self.channels_tablewidget.setRowCount(0)

        self.sequence_diagram_plot.clear()
        self.loop_duration_label.setText("Duration: ( )")
        self.current_iteration_label.setText("current iteration: ( )")
        self.clear_channels_signal.emit()

    def _set_max_iteration_end(self):
        """
        This function is called when the user changes the start time of the iteration.
        It sets the maximum end time of the iteration.
        """

        self.iteration_end_spinbox.setMinimum(
            self.iteration_start_spinbox.value() + 1
        )

    def create_frame(self, tags_colors, sequences_all_channels, frame_i, max_end_time):

        frame = Frame(tags_colors, sequences_all_channels, frame_i, max_end_time)
        frame.display_frame()  # here we send the value to build the Frame
        sequence_for_graph = frame.plot_sequences
        for sequence_frame in sequence_for_graph:
            self.sequence_diagram_plot.addItem(sequence_frame)

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

        

class Frame(QObject):
    """
    This class corresponds to the architecture of a frame
      of the graph for a particular variation. It recieves
      max_end time of al the variation, because otherwise
      as you create frames the pulses to the user might seem
      to change even though they are fixed because of having each
      frame a different end time.
    """

    def __init__(self, channel_tags_colors, sequences, variation, max_end):
        super().__init__()
        self.channel_tags_colors = channel_tags_colors  # [channel.tag,channel.label]
        self.sequences = sequences
        self.variation = variation
        self.plot_sequences = []
        self.max_end = max_end

    def display_frame(self):
        """
        Plots sequences of pulses as stacked Heaviside (step) functions
        into the provided pyqtgraph PlotWidget.

        Parameters:
        - graphWidget: a pg.PlotWidget instance (e.g. self.ui.graphWidget)
        - sequences: list of lists of Pulse objects, one list per channel
        """
        # First, find the global end time (latest end time across all pulses)
        global_end = 0
        for seq in self.sequences:
            for pulse in seq:
                if pulse.end_tail > global_end:
                    global_end = pulse.end_tail
        global_end = max(global_end, self.max_end)  # Ensure global_end is at least max_end
        for i, seq in enumerate(self.sequences):
            color = self.channel_tags_colors[i][1]
            if color == "red":
                color = "r"
            elif color == "green":
                color = "g"
            elif color == "yellow":
                color = "yellow"
            elif color == "orange":
                color = "#FF5733"
            elif color == "blue":
                color = "blue"
            elif color == "pink":
                color = "pink"
            elif color == "white":
                color = "white"
            elif color == "apd":
                color = "orange"
            elif color == "microwave":
                color = "microwave"
            x = []  # x-axis values (time)
            y = []  # y-axis values (level for Heaviside + offset)

            offset = 2 * i  # vertical space between channels

            # Sort the pulses in this channel by start time
            seq = sorted(seq, key=lambda p: p.start_tail)

            last_end = 0  # Tracks the end of the last pulse to detect gaps

            for pulse in seq:
                # If there is a gap before the next pulse, draw a flat line at 0
                if pulse.start_tail > last_end:
                    x.extend([last_end, pulse.start_tail])
                    y.extend([offset, offset])  # Flat baseline

                # Rising edge: step up at start
                x.append(pulse.start_tail)
                y.append(offset)

                x.append(pulse.start_tail)
                y.append(offset + 1)

                # High level: flat line from start to end
                x.append(pulse.end_tail)
                y.append(offset + 1)

                # Falling edge: step down at end
                x.append(pulse.end_tail)
                y.append(offset)

                last_end = pulse.end_tail  # Update the last end for gap checking
            # If the last pulse ends before the global end, extend the flat line
            if last_end < global_end:
                x.extend([last_end, global_end])
                y.extend([offset, offset])
            # Optionally, draw a flat tail after the last pulse
            # x.append(last_end + 1)
            # y.append(offset)
            # Ensure x has one more element than y
            x.append(global_end)
            # y.append(offset)
            # Create a PlotDataItem with step mode to mimic Heaviside function
            plot_item = pg.PlotDataItem(
                x,
                y,
                stepMode=True,  # Important for square wave behavior
                pen={"color": color, "width": 2},  # Line thickness
            )

            # Add the pulse trace to frame list
            self.plot_sequences.append(plot_item)
            channel_tag = str(
                self.channel_tags_colors[i][0]
            )  # Assuming the first element is the tag
            text_item = pg.TextItem(
                text=channel_tag,
                color=color,  # Match the text color to the line color
                anchor=(0, 1),  # Align the text to the top left
            )
            text_item.setPos(
                x[0], offset + 1.25
            )  # Position the text slightly above the sequence
            self.plot_sequences.append(
                text_item
            )  # Add the TextItem to the sequence list


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = PulsedESRMainWindow()
    widget.show()
    sys.exit(app.exec_())
