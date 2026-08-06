from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QColor, QIcon, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QWidget

from .structures import CHANNEL_COLOR_PALLETTE, Channel, Pulse, Sequence
from .ui.ui_creator import Ui_CreatorWidget


class SequenceCreator(QWidget, Ui_CreatorWidget):
    added_channel_sig = Signal(Channel)
    selected_channel_sig = Signal(Channel)
    added_pulse_sig = Signal(Pulse)
    max_iterations_sig = Signal(int)
    sequence_name_changed = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sequence: Sequence = None
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
        self.clear()
        for channel in self.sequence.channels.values():
            self.add_channel_to_list(channel)

    @property
    def channels(self):
        return self.sequence.channels

    @property
    def pulses(self):
        return self.sequence.pulses

    def init_ui(self):

        self.add_channel_button.clicked.connect(self.register_channel)
        self.add_pulse_btn.clicked.connect(self.register_pulse)
        self.channels_list.itemSelectionChanged.connect(
            self.handle_channel_selection_changed
        )
        self.iterations_spin.setValue(100)
        self.iterations_spin.valueChanged.connect(self.max_iterations_sig.emit)
        self.seq_name_edit.returnPressed.connect(self.handle_sequence_name_edit)

    @Slot()
    def handle_sequence_name_edit(self):

        new_name = self.seq_name_edit.text()
        self.set_sequence_name(new_name)

    def set_sequence_name(self, new_name):
        self.seq_name_edit.setText(new_name)
        self.sequence.name = new_name
        self.sequence_name_changed.emit(self.sequence.name)

    def register_channel(self):
        name = f"Channel_{len(self.channels)}"
        if not name or name in self.channels:
            return
        hw_id = len(self.channels)
        color = CHANNEL_COLOR_PALLETTE["default"]

        channel = Channel(name=name, pb_id=hw_id, color=color)
        self.sequence.add_channel(channel)
        self.add_channel_to_list(channel)
        self.added_channel_sig.emit(channel)

    def add_channel_to_list(self, channel: Channel):

        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(*channel.color))  # e.g. (255, 0, 0) for red

        item = QListWidgetItem(QIcon(pixmap), f"[PB{channel.pb_id}]  {channel.name}")
        item.setData(Qt.ItemDataRole.UserRole, channel)
        self.channels_list.addItem(item)
        self.channels_list.setCurrentItem(item)

        self.channels_list.sortItems(Qt.SortOrder.AscendingOrder)

    def handle_channel_selection_changed(self):
        selected_channel_items = self.channels_list.selectedItems()
        if not selected_channel_items:
            return

        selected_item = selected_channel_items[0]
        selected_channel: Channel = selected_item.data(Qt.ItemDataRole.UserRole)
        self.selected_channel_sig.emit(selected_channel)

    def update_channels_list(self, channel: Channel):
        for index in range(self.channels_list.count()):
            item = self.channels_list.item(index)
            item_channel: Channel = item.data(Qt.ItemDataRole.UserRole)
            if item_channel.uid == channel.uid:
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor(*channel.color))
                item.setIcon(QIcon(pixmap))
                item.setText(f"[PB{channel.pb_id}]  {channel.name}")
                break

        self.channels_list.sortItems(Qt.SortOrder.AscendingOrder)

    def remove_channel_from_list(self, channel: Channel):
        for index in range(self.channels_list.count()):
            item = self.channels_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole).uid == channel.uid:
                # takeItem safely removes it from the QListWidget
                self.channels_list.takeItem(index)
                break

    def clear(self):
        self.channels_list.clear()
        self.sequence.channels.clear()

    def register_pulse(self):

        channel = self.channels_list.currentItem().data(Qt.ItemDataRole.UserRole)
        pulse: Pulse = channel.add_pulse(start=200, duration=200)
        self.added_pulse_sig.emit(pulse)
