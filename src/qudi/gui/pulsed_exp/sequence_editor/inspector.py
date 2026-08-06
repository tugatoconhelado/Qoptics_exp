from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QWidget

from .structures import CHANNEL_COLOR_PALLETTE, Channel, Pulse, Sequence
from .ui.ui_inspector import Ui_InspectorWidget


class Inspector(QWidget, Ui_InspectorWidget):
    updated_channel_sig = Signal(Channel)
    updated_pulse_sig = Signal(Pulse)
    deleted_pulse_sig = Signal(Pulse)
    deleted_channel_sig = Signal(Channel)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Inspector")
        self.resize(300, 400)
        self._sequence = None
        self.selected_channel: Channel = None
        self.selected_pulse: Pulse = None

        self.setupUi(self)
        self.init_ui()

    @property
    def sequence(self) -> Sequence:
        if self._sequence is None:
            self._sequence = Sequence()
        return self._sequence

    @sequence.setter
    def sequence(self, value: Sequence):
        self._sequence = value

    @property
    def channels(self):
        return self.sequence.channels

    @property
    def pulses(self):
        return self.sequence.pulses

    def init_ui(self):

        self.pb_id_combo.addItems([f"PB{i}" for i in range(20)])

        self.pb_id_combo.currentIndexChanged.connect(self.update_channel)
        self.channel_name_edit.editingFinished.connect(self.update_channel)
        self.delay_on_spin.valueChanged.connect(self.update_channel)
        self.delay_off_spin.valueChanged.connect(self.update_channel)

        self.start_spin.editingFinished.connect(self.update_pulse)
        self.duration_spin.editingFinished.connect(self.update_pulse)
        self.channel_combo.currentIndexChanged.connect(self.update_pulse)

        self.sweep_box.clicked.connect(self.update_pulse)
        self.sweep_start_edit.editingFinished.connect(self.update_pulse)
        self.sweep_duration_edit.editingFinished.connect(self.update_pulse)
        self.ripple_combo.currentIndexChanged.connect(self.update_pulse)

        self.delete_pulse_btn.clicked.connect(self.request_pulse_deletion)

    def remove_channel_from_combo(self, channel: Channel):
        """Clean up the combobox when a channel is destroyed."""
        for i in range(self.channel_combo.count()):
            if self.channel_combo.itemData(i) == channel.uid:
                self.channel_combo.removeItem(i)
                break

    # -------------------------------------------------------------------------
    # Channel Inspector
    # -------------------------------------------------------------------------

    @Slot(Channel)
    def display_channel(self, channel: Channel):
        self._block_signals(True)
        self.selected_channel: Channel = channel
        self.channel_name_edit.setText(channel.name)
        self.pb_id_combo.setCurrentIndex(channel.pb_id)
        self.delay_on_spin.setValue(channel.delay[0])
        self.delay_off_spin.setValue(channel.delay[1])
        self._block_signals(False)

    def update_channel(self):
        if self.selected_channel:
            new_name = self.channel_name_edit.text()
            self.selected_channel.name = new_name
            self.selected_channel.pb_id = self.pb_id_combo.currentIndex()
            self.selected_channel.delay = (
                self.delay_on_spin.value(),
                self.delay_off_spin.value(),
            )

            if new_name in CHANNEL_COLOR_PALLETTE:
                self.selected_channel.color = CHANNEL_COLOR_PALLETTE[new_name]
            self.updated_channel_sig.emit(self.selected_channel)

    def request_channel_deletion(self):
        if self.selected_channel:
            self.deleted_channel_sig.emit(self.selected_channel)

    # -------------------------------------------------------------------------
    # Pulse Inspector
    # -------------------------------------------------------------------------

    @Slot(Channel)
    def add_channel_to_combo(self, channel: Channel):
        self.channel_combo.addItem(channel.name, channel.uid)

    @Slot(Channel)
    def update_channel_in_combo(self, channel: Channel):
        """Finds the combo item by UID and updates its text."""
        for i in range(self.channel_combo.count()):
            if self.channel_combo.itemData(i) == channel.uid:
                self.channel_combo.setItemText(i, channel.name)
                break

    @Slot(Pulse)
    def display_pulse(self, pulse: Pulse):
        self._block_signals(True)
        self.selected_pulse: Pulse = pulse

        self.start_spin.setValue(pulse.start)
        self.duration_spin.setValue(pulse.duration)
        channel_index = list(self.channels.keys()).index(pulse.channel.uid)
        self.channel_combo.setCurrentIndex(channel_index)

        self.sweep_start_edit.setText(pulse.start_sweep)
        self.sweep_duration_edit.setText(pulse.duration_sweep)
        ripple_idx = 0
        if pulse.ripple == "channel":
            ripple_idx = 1
        elif pulse.ripple == "global":
            ripple_idx = 2
        self.ripple_combo.setCurrentIndex(ripple_idx)

        has_sweep = bool(pulse.start_sweep or pulse.duration_sweep)
        self.sweep_box.setChecked(has_sweep)

        self.display_channel(pulse.channel)
        self._block_signals(False)

    @Slot()
    def update_pulse(self):
        if self.selected_pulse:
            self.selected_pulse.start = self.start_spin.value()
            self.selected_pulse.duration = self.duration_spin.value()

            if self.sweep_box.isChecked():
                start_sweep = self.sweep_start_edit.text().strip()
                duration_sweep = self.sweep_duration_edit.text().strip()

                self.selected_pulse.start_sweep = start_sweep
                self.selected_pulse.duration_sweep = duration_sweep
                self.selected_pulse.ripple: str = (
                    self.ripple_combo.currentText().lower()
                )

            else:
                self.selected_pulse.start_sweep = ""
                self.selected_pulse.duration_sweep = ""
                self.selected_pulse.ripple = "none"

            channel_id = self.channel_combo.currentData()
            if channel_id not in self.channels.keys():
                return

            new_channel = self.channels[channel_id]
            self.selected_pulse.move_to_channel(new_channel)
            self.updated_pulse_sig.emit(self.selected_pulse)

    def request_pulse_deletion(self):
        if self.selected_pulse:
            self.deleted_pulse_sig.emit(self.selected_pulse)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _block_signals(self, block: bool):
        self.pb_id_combo.blockSignals(block)
        self.channel_name_edit.blockSignals(block)
        self.delay_on_spin.blockSignals(block)
        self.delay_off_spin.blockSignals(block)
        self.start_spin.blockSignals(block)
        self.duration_spin.blockSignals(block)
        self.channel_combo.blockSignals(block)
        self.sweep_box.blockSignals(block)
        self.sweep_duration_edit.blockSignals(block)
        self.sweep_start_edit.blockSignals(block)
        self.ripple_combo.blockSignals(block)
