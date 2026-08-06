import json

from PySide2.QtCore import QTimer, Slot, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QFileDialog,
    QMainWindow,
)

from .structures import Channel, Pulse, Sequence
from .ui.ui_editor import Ui_SequenceEditorMainWindow


class SequenceEditor(QMainWindow, Ui_SequenceEditorMainWindow):

    seq_name_sig = Signal(str)
    sequence_changed = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.sequence = Sequence()

        self.init_ui()

    @property
    def channels(self):
        return self.sequence.channels

    @property
    def pulses(self):
        return self.sequence.pulses

    def init_ui(self):

        self.sequence_plot.sequence = self.sequence
        self.sequence_creator.sequence = self.sequence
        self.inspector.sequence = self.sequence

        self.sequence_creator.added_channel_sig.connect(self.handle_channel_created)
        self.sequence_creator.added_pulse_sig.connect(self.handle_pulse_created)
        self.sequence_creator.selected_channel_sig.connect(
            self.inspector.display_channel
        )
        self.sequence_creator.max_iterations_sig.connect(self.set_simulation_iteration_range)

        self.sequence_creator.sequence_name_changed.connect(self.seq_name_sig.emit)

        self.inspector.updated_channel_sig.connect(
            self.handle_channel_update_from_inspector
        )
        self.inspector.updated_pulse_sig.connect(self.handle_pulse_updated)
        self.inspector.deleted_pulse_sig.connect(self.handle_pulse_deleted)
        self.inspector.deleted_channel_sig.connect(self.handle_channel_deleted)

        self.sequence_plot.pulse_selected_sig.connect(self.inspector.display_pulse)
        self.sequence_plot.pulse_created_sig.connect(self.handle_pulse_created)
        self.sequence_plot.delete_pulse_sig.connect(self.handle_pulse_deleted)

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.step_slider_forward)
        self.iteration_spin.valueChanged.connect(self.simulate_sequence)
        self.play_btn.toggled.connect(self.toggle_playback)

        self.open_action.triggered.connect(self.prompt_open_file)
        self.save_action.triggered.connect(self.prompt_save_file)
        self.clear_action.triggered.connect(self.clear)

        self.sequence_creator.load_sequence_btn.clicked.connect(self.prompt_open_file)
        self.sequence_creator.save_sequence_btn.clicked.connect(self.prompt_save_file)

    def prompt_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Sequence", "C:\EXP\data\sequences", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            print(f"Loading sequence from file: {file_path}")
            with open(file_path, "r") as f:
                data = json.load(f)
            new_sequence = Sequence.from_dict(data)
            self.load_sequence(new_sequence)

        except Exception as e:
            print(f"Error loading sequence from file: {e}")

    def prompt_save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Sequence", "C:\EXP\data\sequences", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            print(f"Saving sequence to {file_path}")
            data = self.sequence.to_dict()
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"Error saving sequence to file: {e}")

    def load_sequence(self, new_sequence: Sequence):

        self.clear()

        # Re-add channels and pulses to the plot
        for channel in new_sequence.channels.values():
            self.sequence.add_channel(channel)
            self.sequence_plot.add_channel_to_plot(channel)
            self.inspector.add_channel_to_combo(channel)
            self.sequence_creator.add_channel_to_list(channel)

            for pulse in channel.pulses:
                self.sequence.add_pulse(pulse)
                self.sequence_plot.add_pulse_to_plot(pulse)
        self.sequence.iterations = new_sequence.iterations
        self.sequence_creator.iterations_spin.setValue(self.sequence.iterations)
        self.sequence_creator.set_sequence_name(new_sequence.name)

        self.sequence_changed.emit()

    def clear(self):
        # Clear existing plot items
        self.sequence_plot.clear()
        self.sequence_creator.clear()

    @Slot(Channel)
    def handle_channel_created(self, channel: Channel):
        self.sequence_plot.add_channel_to_plot(channel)
        self.inspector.add_channel_to_combo(channel)
        self.inspector.display_channel(channel)

        # Shift keyboard focus directly to the Inspector
        self.inspector.channel_name_edit.setFocus()
        self.inspector.channel_name_edit.selectAll()

        self.sequence_changed.emit()

    @Slot(Pulse)
    def handle_pulse_created(self, pulse: Pulse):
        self.sequence_plot.add_pulse_to_plot(pulse)
        self.inspector.display_pulse(pulse)

        # Shift keyboard focus directly to the Start Position spinbox
        self.inspector.start_spin.setFocus()
        self.inspector.start_spin.selectAll()
        self.sequence_changed.emit()

    @Slot(Channel)
    def handle_channel_update_from_inspector(self, channel: Channel):
        self.sequence_creator.update_channels_list(channel)
        self.sequence_plot.update_channel_visuals(channel)
        self.inspector.update_channel_in_combo(channel)
        self.sequence_changed.emit()

    def handle_pulse_updated(self, pulse: Pulse):
        self.sequence_plot.update_pulse_plot(pulse)
        self.sequence_changed.emit()

    @Slot(Channel)
    def handle_channel_deleted(self, channel: Channel):
        self.sequence.channels.pop(channel.uid, None)

        self.sequence_creator.remove_channel_from_list(channel)
        self.sequence_plot.remove_channel_from_plot(channel)
        self.inspector.remove_channel_from_combo(channel)
        self.sequence_changed.emit()

    @Slot(Pulse)
    def handle_pulse_deleted(self, pulse: Pulse):
        pulse.channel.remove_pulse(pulse)
        if pulse in self.sequence.pulses:
            self.sequence.pulses.remove(pulse)

        self.sequence_plot.remove_pulse_from_plot(pulse)
        self.sequence_changed.emit()

    @Slot(int)
    def simulate_sequence(self, iteration: int):
        simulated_seq = self.sequence.evaluate_iteration(iteration)
        self.sequence_plot.display_simulation(simulated_seq)

    def toggle_playback(self, checked: bool):
        if checked:
            # Button is pressed DOWN -> Start playing and change icon to Pause
            self.playback_timer.start(30)
            pause_icon = QIcon.fromTheme("media-playback-pause")
            self.play_btn.setIcon(pause_icon)

            if self.sim_slider.value() == self.sim_slider.maximum():
                self.sim_slider.setValue(0)
        else:
            # Button is popped UP -> Stop playing and change icon back to Play
            self.playback_timer.stop()
            play_icon = QIcon.fromTheme("media-playback-start")
            self.play_btn.setIcon(play_icon)

    @Slot(int)
    def set_simulation_iteration_range(self, iterations: int):
        self.sim_slider.setMaximum(iterations)
        self.iteration_spin.setMaximum(iterations)
        self.sequence.iterations = iterations

    def step_slider_forward(self):
        current_value = self.sim_slider.value()
        if current_value < self.sim_slider.maximum():
            self.sim_slider.setValue(current_value + 1)

        if current_value == self.sim_slider.maximum():
            if self.play_btn.isChecked():
                self.play_btn.setChecked(False)

    @Slot()
    def start_playback(self):
        self.playback_timer.start(30)

    @Slot()
    def stop_playback(self):
        self.playback_timer.stop()
