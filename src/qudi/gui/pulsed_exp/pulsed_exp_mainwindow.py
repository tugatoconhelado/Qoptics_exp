from PySide2.QtWidgets import QDialog, QWidget, QMainWindow, QApplication, QTableWidgetItem, QFileDialog
from PySide2.QtCore import Slot, Signal, QDir, QObject
from PySide2.QtGui import QFont
from qudi.util.uic import loadUi
import numpy as np
import pyqtgraph as pg
import sys
import os


class PulsedExpMainWindow(QMainWindow):
    """
    Main Window of the TimeTrace Experiment
    """

    start_experiment_signal = Signal(int, float, float)
    pb_output_status_signal = Signal(tuple)
    pb_output_stop_signal = Signal()
    update_channels_signal = Signal(list)
    update_pulses_signal = Signal(list)
    clear_channels_signal = Signal()
    load_seq_file_signal = Signal(str)
    save_seq_file_signal = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.join(os.path.dirname(__file__), "pulsed_exp.ui"), self)

        self.iteration_start_spinbox.valueChanged.connect(self._set_max_iteration_end)
        self.stop_output_button.clicked.connect(self.pb_output_stop_signal.emit)
        self.run_output_button.clicked.connect(self._get_output_state)
        self.clear_channels_button.clicked.connect(self._clear_gui)
        self.clear_channels_button.clicked.connect(self.clear_channels_signal.emit)
        self.load_sequence_button.clicked.connect(self._load_sequence)
        self.save_sequence_button.clicked.connect(self._save_sequence)

        self.pulse_width_spinbox.setValue(20e-9)
        self.start_time_spinbox.setValue(10e-9)

        self.update_channels_button.clicked.connect(self._update_channels)
        self.update_pulses_button.clicked.connect(self._update_pulses)

        self.plotter = SequencePlotter()
        self.configure_plots()

    def configure_plots(self):

        self.pulsed_exp_dataline = self.pulsed_exp_plot.plot([], pen='yellow')
        self.pulsed_exp_plot.setLabel('left', 'Counts')

        self.errorbars = pg.ErrorBarItem(pen=(31, 119, 180), beam=0.3)
        self.pulsed_exp_plot.addItem(self.errorbars)

        self.sequence_diagram_plot.getPlotItem().hideAxis('left')

    @Slot(str)
    def update_status_bar(self, msg: str):
        self.statusbar.showMessage(msg)

    @Slot(np.ndarray, np.ndarray, np.ndarray)
    def update_pulsed_exp_plot(self, x: np.ndarray, y: np.ndarray, st_dev: np.ndarray):
        """
        Update the pulsed experiment plot with new data.
        """
        y = y.flatten()
        self.pulsed_exp_dataline.setData(x, y)
        self.errorbars.setData(x=x, y=y, height=2 * st_dev)
        self.pulsed_exp_plot.setYRange(min(y), max(y))

    @Slot()
    def _clear_gui(self):

        self.channels_tablewidget.clearContents()
        self.channels_tablewidget.setRowCount(0)

        self.pulses_tablewidget.clearContents()
        self.pulses_tablewidget.setRowCount(0)

        self.sequence_diagram_plot.clear()
        self.loop_duration_label.setText("Duration: ( )")
        self.current_iteration_label.setText("current iteration: ( )")

    def _set_max_iteration_end(self):
        """
        This function is called when the user changes the start time of the iteration.
        It sets the maximum end time of the iteration.
        """

        self.iteration_end_spinbox.setMinimum(
            self.iteration_start_spinbox.value() + 1
        )

    @Slot(list, list, int, int)
    def create_frame(self, tags_colors, sequences_all_channels, frame_i, max_end_time):

        frame = Frame(tags_colors, sequences_all_channels, frame_i, max_end_time)
        frame.display_frame() 
        sequence_for_graph = frame.plot_sequences
        for sequence_frame in sequence_for_graph:
            self.sequence_diagram_plot.addItem(sequence_frame)

    def new_create_frame(self, channel_tags_colors, sequences, variation, max_end):

        """
        This function creates a new frame for the sequence diagram plot.
        It receives the channel tags and colors, sequences, variation and max_end time.
        """
        self.plotter.test_plot_sequence(self.sequence_diagram_plot, channel_tags_colors, sequences, max_end)
    @Slot(str)
    def add_iteration_text(self, text):
        self.current_iteration_label.setText(text)
    
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

    @Slot(int, float, float, str, str, int, int)
    def update_pulse_table(self, channel, start, width, function_start, function_width, i_start, i_end):

        i = self.pulses_tablewidget.rowCount()
        self.pulses_tablewidget.insertRow(i)

        self.pulses_tablewidget.setItem(
            i, 0, QTableWidgetItem("PB" + str(channel))
        )
        self.pulses_tablewidget.setItem(
            i, 1, QTableWidgetItem(str(start))
        )
        self.pulses_tablewidget.setItem(
            i, 2, QTableWidgetItem(str(width))
        )
        self.pulses_tablewidget.setItem(
            i, 3, QTableWidgetItem(str(function_start))
        )
        self.pulses_tablewidget.setItem(
            i, 4, QTableWidgetItem(str(function_width))
        )
        self.pulses_tablewidget.setItem(
            i, 5, QTableWidgetItem(str(i_start))
        )
        self.pulses_tablewidget.setItem(
            i, 6, QTableWidgetItem(str(i_end))
        )

    @Slot(int, int, int, str)
    def update_channels_table(self, channel, delay_on, delay_off, type):

        i = self.channels_tablewidget.rowCount()
        self.channels_tablewidget.insertRow(i)

        self.channels_tablewidget.setItem(
            i, 0, QTableWidgetItem("PB" + str(channel))
        )
        self.channels_tablewidget.setItem(
            i, 1, QTableWidgetItem(str(delay_on))
        )
        self.channels_tablewidget.setItem(
            i, 2, QTableWidgetItem(str(delay_off))
        )
        self.channels_tablewidget.setItem(
            i, 3, QTableWidgetItem(type)
        )

    def _load_sequence(self):

        file_dir = os.path.join(os.sep, "c:" + os.sep, "EXP", "data", "sequences")
        dialog = QFileDialog(self)
        directory = file_dir
        dialog.setDirectory(directory)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter('JSON files (*.json)')
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec_():
            file_path = dialog.selectedFiles()[0]
            file_type = dialog.selectedNameFilter()
        else:
            return ''
        
        self.load_seq_file_signal.emit(file_path)
        filename = os.path.basename(file_path)
        filename = os.path.splitext(filename)[0]
        self.sequence_name_label.setText(filename)
        return os.path.abspath(file_path)
    
    def _save_sequence(self):
        """
        This function is called when the user clicks the "Save" button.
        It saves the current sequence to a file.
        """
        file_dir = os.path.join(os.sep, "c:" + os.sep, "EXP", "data", "sequences")
        dialog = QFileDialog(self)
        directory = file_dir
        dialog.setDirectory(directory)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setNameFilter('JSON files (*.json)')
        dialog.setViewMode(QFileDialog.ViewMode.List)
        dialog.setDefaultSuffix('.json')
        if dialog.exec_():
            file_path = dialog.selectedFiles()[0]
            file_type = dialog.selectedNameFilter()
        else:
            return ''
        self.save_seq_file_signal.emit(file_path)
        filename = os.path.basename(file_path)
        filename = os.path.splitext(filename)[0]
        self.sequence_name_label.setText(filename)
        return os.path.abspath(file_path)

    @Slot()
    def _update_channels(self):

        updated_channels = []

        for row in range(self.channels_tablewidget.rowCount()):
            item = self.channels_tablewidget.item(row, 0)
            if item is None:
                continue
            channel_tag = item.text()
            channel_tag = int(channel_tag[2:])
            delay_on = self.channels_tablewidget.item(row, 1).text()
            delay_off = self.channels_tablewidget.item(row, 2).text()
            delay_on = float(delay_on) if delay_on else 0.0
            delay_off = float(delay_off) if delay_off else 0.0
            delay = [delay_on, delay_off]
            channel_type = self.channels_tablewidget.item(row, 3).text()
            print(f"Channel {channel_tag} modified: delay_on={delay_on}, delay_off={delay_off}, type={channel_type}")
            updated_channels.append(
                [channel_tag, delay, channel_type]
            )
        if len(updated_channels) != 0:
            self._clear_gui()
            self.update_channels_signal.emit(updated_channels)
            
    def _update_pulses(self):

        updated_pulses = []
        for row in range(self.pulses_tablewidget.rowCount()):

            channel = self.pulses_tablewidget.item(row, 0).text()
            channel = int(channel[2:])
            start_time = self.pulses_tablewidget.item(row, 1).text()
            pulse_width = self.pulses_tablewidget.item(row, 2).text()
            function_width = self.pulses_tablewidget.item(row, 3).text()
            function_start = self.pulses_tablewidget.item(row, 4).text()
            i_start = self.pulses_tablewidget.item(row, 5).text()
            i_end = self.pulses_tablewidget.item(row, 6).text()
            i_start = int(i_start) if i_start else 0
            i_end = int(i_end) if i_end else 0
            iteration_range = [i_start, i_end]
            pulse = [
                channel,
                float(start_time) if start_time else 0.0,
                float(pulse_width) if pulse_width else 0.0,
                function_width,
                function_start,
                iteration_range
            ]
            updated_pulses.append(pulse)
        if len(updated_pulses) != 0:
            self.pulses_tablewidget.clearContents()
            self.pulses_tablewidget.setRowCount(0)
            self.update_pulses_signal.emit(updated_pulses)


class SequencePlotter(QObject):

    def __init__(self):
        super().__init__()
        self.pulses = []
        self.sequences = []

    def test_plot_sequence(self, plot_widget, channel_tags_colors, sequences, max_end):

        global_end = 0
        for seq in sequences:
            for pulse in seq:
                if pulse.end_tail > global_end:
                    global_end = pulse.end_tail
        global_end = max(global_end, max_end)  # Ensure global_end is at least max_end

        self.sequences = sequences  # Store sequences for later use

        for i, seq in enumerate(sequences):
            color = channel_tags_colors[i][1]
            if color == "orange":
                color = "#FF5733"
            elif color == "apd":
                color = "orange"
            elif color == "microwave":
                color = "microwave"
            elif color == 'red':
                color = 'r'
            elif color == 'blue':
                color = 'b'
            elif color == 'green':
                color = 'g'

            x = []  # x-axis values (time)
            y = []  # y-axis values (level for Heaviside + offset)

            offset = 2 * i  # vertical space between channels

            # Sort the pulses in this channel by start time
            seq = sorted(seq, key=lambda p: p.start_tail)

            last_end = 0  # Tracks the end of the last pulse to detect gaps

            #for pulse in seq:
                #roi = pg.ROI(
                #    pos = [pulse.start_tail, offset],
                #    size = [pulse.end_tail - pulse.start_tail, 1],
                #    movable=False,
                #    resizable=False,
                #    rotatable=False,
                #    removable=False,
                #    pen=pg.mkPen(color=color, width=2),
                #)
                #roi.addScaleHandle([1, 0.5], [0, 0.5])  # Add a handle at the right side
                #plot_widget.addItem(roi)
                #if pulse.start_tail > last_end:
                #    x.extend([last_end, pulse.start_tail])
                #    y.extend([offset, offset])
            # If the last pulse ends before the global end, extend the flat line
            #if last_end < global_end:
            #    x.extend([last_end, global_end])
            #    y.extend([offset, offset])

            #x.append(global_end)
            #print(x)
            #print(y)
            for pulse in seq:
                pulse_plot = PulsePlot(
                    start=pulse.start_tail,
                    width=pulse.end_tail - pulse.start_tail,
                    baseline=offset,
                    plot_widget=plot_widget,
                    color=color
                )
                self.pulses.append(pulse_plot)

            channel_tag = 'PB' + str(channel_tags_colors[i][0])  
            text_item = pg.TextItem(
                text=channel_tag,
                color=color,  # Match the text color to the line color
                anchor=(1, 0.5)
            )
            text_item.setPos(0, offset + 0.5)
            text_item.setFont(QFont("Arial", 20))
            plot_widget.addItem(text_item)


    def plot_sequence(self, plot_widget, channel_tags_colors, sequences, max_end):

        # First, find the global end time (latest end time across all pulses)
        global_end = 0
        for seq in sequences:
            for pulse in seq:
                if pulse.end_tail > global_end:
                    global_end = pulse.end_tail
        global_end = max(global_end, max_end)  # Ensure global_end is at least max_end

        for i, seq in enumerate(sequences):
            color = channel_tags_colors[i][1]
            if color == "orange":
                color = "#FF5733"
            elif color == "apd":
                color = "orange"
            elif color == "microwave":
                color = "microwave"
            elif color == 'red':
                color = 'r'
            elif color == 'blue':
                color = 'b'
            elif color == 'green':
                color = 'g'

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

            x.append(global_end)
            print(x)
            print(y)
            plot_item = pg.PlotDataItem(
                x,
                y,
                stepMode='center',  # Important for square wave behavior
                pen={"color": color, "width": 2},  # Line thickness
            )

            # Add the pulse trace to frame list
            plot_widget.addItem(plot_item)

            channel_tag = 'PB' + str(channel_tags_colors[i][0])  
            text_item = pg.TextItem(
                text=channel_tag,
                color=color,  # Match the text color to the line color
                anchor=(0.5, 0.5)  # Align the text to the top left
            )
            text_item.setPos(0, offset + 0.5)
            text_item.setFont(QFont("Arial", 20))
            plot_widget.addItem(text_item)


class CustomROI(pg.ROI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_moved_handle = None

    def movePoint(self, handle, pos, modifiers=(), **kwargs):
        self.last_moved_handle = handle
        super().movePoint(handle, pos, modifiers, **kwargs)


class PulsePlot(QObject):
    def __init__(self, start, width, baseline, plot_widget=None, color='y'):
        super().__init__()

        self.plot_widget = plot_widget
    
        self.duration = 200
        self.amplitude = 1
        self.snap_step = 2
        self.min_width = 2
        self.x = np.linspace(0, self.duration, 1000)

        self.start = start
        self.width = width
        self.baseline = baseline
        self.height = 0.001

        # Use custom ROI to track handle
        self.roi = CustomROI([self.start, self.baseline + 0.5 - self.height / 2], [self.width, self.height], movable=True, pen='r')
        self.plot_widget.addItem(self.roi)

        # Add scale handles and keep references
        self.left_handle = self.roi.addScaleHandle([0, 0.5], [1, 0.5])   # left
        self.right_handle = self.roi.addScaleHandle([1, 0.5], [0, 0.5])  # right

        self.roi.sigRegionChanged.connect(self.snap_and_update)

        self.rect_curve = self.plot_widget.plot(pen=color)

        self.update_plot()

    def rectangular_signal(self, x, start, width, amplitude):
        return np.where((x >= start) & (x <= start + width), amplitude, 0)

    def update_plot(self):
        y = self.rectangular_signal(self.x, self.start, self.width, self.amplitude)
        y = y + self.baseline  # Adjust height of the pulse
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
        self.roi.setPos([self.start, self.baseline + 0.5 - self.height / 2])
        self.roi.setSize([self.width, self.height])
        self.roi.blockSignals(False)

        self.update_plot()


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
            if color == "orange":
                color = "#FF5733"
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

            x.append(global_end)

            plot_item = pg.PlotDataItem(
                x,
                y,
                stepMode='center',  # Important for square wave behavior
                pen={"color": color, "width": 2},  # Line thickness
            )

            # Add the pulse trace to frame list
            self.plot_sequences.append(plot_item)
            channel_tag = 'PB' + str(self.channel_tags_colors[i][0])  
            text_item = pg.TextItem(
                text=channel_tag,
                color=color,  # Match the text color to the line color
                anchor=(0, 1),  # Align the text to the top left
            )
            #text_item.setFlag(text_item.GraphicsItemFlag.ItemIgnoresTransformations, True)
            text_item.setPos(
                x[0], offset
            )  # Position the text slightly above the sequence
            self.plot_sequences.append(
                text_item
            )


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication
    print(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    import artwork.qudi_icons_rc
    from qudi.logic.pulsed_exp_logic import Pulse

    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = PulsedExpMainWindow()
    widget.show()

    sequences = [
        [
            Pulse(10, 20, 0),
            Pulse(50, 80, 1),   
        ],
        [
            Pulse(15, 25, 0),
            Pulse(55, 75, 1),
        ],
    ]
    tags_colors = [
        [0, "green"],
        [1, "apd"],
    ]
    widget.new_create_frame(tags_colors, sequences, 0, 100)
    sys.exit(app.exec_())
