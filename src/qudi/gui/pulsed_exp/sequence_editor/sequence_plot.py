import numpy as np
import pyqtgraph as pg
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QVBoxLayout, QWidget

from .region import PulseRegionItem
from .structures import Channel, Pulse, Sequence


class SequencePlot(QWidget):
    pulse_selected_sig = Signal(Pulse)
    pulse_created_sig = Signal(Pulse)
    delete_pulse_sig = Signal(Pulse)

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._sequence: Sequence = None
        self._pulse_regions: list = []
        self._channel_visuals: dict = {}

        self.init_ui()

    @property
    def sequence(self) -> Sequence:
        if self._sequence is None:
            self._sequence = Sequence()
        return self._sequence

    @sequence.setter
    def sequence(self, value: Sequence):
        self._sequence = value
        self._displayed_sequence = value
        for channel in self.sequence.channels.values():
            self.add_channel_to_plot(channel)

    @property
    def channels(self):
        return self.sequence.channels

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.plot = pg.PlotWidget(title="Pulse Sequence")
        self.plot.setLabel("left", "Amplitude")
        self.plot.setLabel("bottom", "Time (ns)")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setMouseEnabled(x=True, y=False)

        view_box = self.plot.getViewBox()
        view_box.setLimits(xMin=0, xMax=None)
        view_box.sigXRangeChanged.connect(self.redraw_all_waveforms)

        self.plot.scene().sigMouseClicked.connect(self.handle_mouse_click)  # type: ignore

        layout.addWidget(self.plot)

    def handle_mouse_click(self, event):
        if event.double() and event.button() == Qt.MouseButton.LeftButton:

            view_box = self.plot.getViewBox()

            # Make sure click inside the actual graph area (not on an axis label)
            if view_box.sceneBoundingRect().contains(event.scenePos()):
                # Convert screen pixels to plot coordinates
                mouse_point = view_box.mapSceneToView(event.scenePos())

                x_time = mouse_point.x()
                y_lane = mouse_point.y()

                # Because lanes are simply integers 0, 1, 2...
                # We can just cast the Y coordinate to an int to find the lane!
                lane_idx = int(y_lane)

                # Verify they actually clicked on a valid lane
                if 0 <= lane_idx < len(self.channels):
                    # Get the channel for this lane
                    channel_uid = list(self.channels.keys())[lane_idx]
                    channel = self.channels[channel_uid]

                    # Snap the time to your hardware tick (e.g. nearest 2ns)
                    start_ns = max(0, round(x_time / 2) * 2)

                    # Generate the pulse with a default duration (e.g. 200ns)
                    pulse = channel.add_pulse(start=int(start_ns), duration=200)

                    # Tell the editor to handle the UI routing
                    self.pulse_created_sig.emit(pulse)

    def get_channel_lane_index(self, channel_uid: str) -> int:
        """Get the index for the Channel lane in the  plot.

        Returns 0 for the first channel, 1 for the second and so on.

        Parameters
        ----------
        channel_uid: str
            The unique identifier of the channel.

        Returns
        -------
        int
            The index of the channel lane in the plot.
        """
        keys = list(self.channels.keys())
        return keys.index(channel_uid)

    @Slot(Channel)
    def add_channel_to_plot(self, channel: Channel):
        name = channel.name
        color = channel.color
        lane_idx = self.get_channel_lane_index(channel.uid)

        trace_line = pg.PlotDataItem(pen=pg.mkPen(color=color, width=2.5))

        track_divider = pg.InfiniteLine(
            pos=lane_idx,
            angle=0,
            pen=pg.mkPen(color=(70, 70, 70), style=Qt.PenStyle.SolidLine),
        )

        label_item = pg.TextItem(text=name, color=color, anchor=(0, 0))
        label_item.setPos(0, lane_idx + 1)

        self.plot.addItem(trace_line)
        self.plot.addItem(track_divider)
        self.plot.addItem(label_item)

        self._channel_visuals[channel.uid] = {"trace": trace_line, "label": label_item}

        self.plot.setYRange(0, len(self.channels), padding=0.1)  # type: ignore

    @Slot(Pulse)
    def add_pulse_to_plot(self, pulse: Pulse):

        lane_idx = self.get_channel_lane_index(pulse.channel.uid)
        visual_region = PulseRegionItem(
            pulse, pulse.channel, self.plot, lane_idx=lane_idx
        )
        visual_region.setBounds([0, None])
        visual_region.sig_pulse_moved.connect(self.on_visual_pulse_interacted)
        visual_region.pulse_selected_sig.connect(self.pulse_selected_sig.emit)
        visual_region.delete_requested_sig.connect(self.delete_pulse_sig.emit)

        self.plot.addItem(visual_region)
        self._pulse_regions.append(visual_region)
        self.update_channel_waveform(pulse.channel)

        self.pulse_selected_sig.emit(pulse)

    @Slot(Pulse)
    def update_pulse_plot(self, pulse: Pulse):
        for region in self._pulse_regions:
            if region.pulse == pulse:
                region_channel = region.channel
                if region.channel != pulse.channel:
                    self.update_channel_waveform(region_channel.uid)

                lane_idx = self.get_channel_lane_index(pulse.channel.uid)
                region.update_region(pulse, lane_idx)

        self.update_channel_waveform(pulse.channel)

    def sync_pulse_spans(self):
        """Ensure that all pulse regions are visually aligned with their channel's vertical span."""
        for region in self._pulse_regions:
            pulse = region.pulse
            vspan = self.sequence.get_channel_span(pulse.channel.uid)
            vspan = (
                vspan[0] / len(self.channels),
                vspan[1] / len(self.channels),
            )
            region.setSpan(*vspan)

    @Slot(Channel, Pulse)
    def on_visual_pulse_interacted(self, channel: Channel, pulse: Pulse):
        self.update_channel_waveform(channel)

    @Slot(Channel)
    def update_channel_visuals(self, channel: Channel):
        """Called when a channel's name or color is edited in the Inspector."""
        visuals = self._channel_visuals.get(channel.uid)
        if not visuals:
            return

        trace_line = visuals["trace"]
        label_item = visuals["label"]

        trace_line.setPen(pg.mkPen(color=channel.color, width=2.5))
        r, g, b = channel.color
        color_hex = f"#{r:02x}{g:02x}{b:02x}"
        label_item.setHtml(f'<div style="color: {color_hex};">{channel.name}</div>')

    def update_channel_waveform(self, channel: Channel):
        #print(f"Updating waveform for channel {channel}")
        if channel.uid not in self._channel_visuals.keys():
            return
        trace_line = self._channel_visuals[channel.uid]["trace"]

        lane_idx = self.get_channel_lane_index(channel.uid)
        baseline_y = lane_idx + 0.1
        high_y = lane_idx + 0.8

        # Merge overlapping pulses into single blocks
        sorted_pulses = sorted(channel.pulses, key=lambda p: p.start)
        merged_intervals = []
        for p in sorted_pulses:
            if not merged_intervals:
                merged_intervals.append([p.start, p.end])
            else:
                last_interval = merged_intervals[-1]
                if p.start <= last_interval[1]:
                    # Extend interval if they overlap
                    last_interval[1] = max(last_interval[1], p.end)
                else:
                    # Create new gap
                    merged_intervals.append([p.start, p.end])

        x_points = []
        y_points = []
        current_time = 0

        # Draw the continuous path (up for pulse, down for gap)
        for start_ns, end_ns in merged_intervals:
            # Draw baseline if there is an empty gap
            if current_time == 0:
                x_points.extend([0, start_ns])
                y_points.extend([baseline_y, baseline_y])

            elif start_ns > current_time:
                x_points.extend([start_ns])
                y_points.extend([baseline_y])

            # Draw the square pulse
            x_points.extend([start_ns, end_ns, end_ns])
            y_points.extend([high_y, high_y, baseline_y])
            current_time = end_ns

        # Add the trailing baseline to the end
        view_end = self.plot.getViewBox().viewRange()[0][1]
        dynamic_end = (
            current_time + max(500, int(current_time * 0.2))
            if current_time > 0
            else 2000
        )
        dynamic_end = view_end * 0.9 if view_end * 0.9 > current_time else current_time
        x_points.extend([dynamic_end])
        y_points.extend([baseline_y])

        trace_line.setData(
            x=np.array(x_points, dtype=float), y=np.array(y_points, dtype=float)
        )

    def redraw_all_waveforms(self):
        """Ensures infinite baselines recalculate lengths when zooming/panning horizontally."""
        for ch in self._displayed_sequence.channels.values():
            self.update_channel_waveform(ch)

    @Slot(Pulse)
    def remove_pulse_from_plot(self, pulse: Pulse):
        for region in self._pulse_regions:
            if region.pulse == pulse:
                self.plot.removeItem(region)
                self._pulse_regions.remove(region)
                break

        # Redraw the solid line without the pulse
        self.update_channel_waveform(pulse.channel)

    @Slot(Channel)
    def remove_channel_from_plot(self, channel: Channel):
        # Because lane heights shift when a channel is removed,
        # the safest way to prevent visual bugs is a quick redraw!
        self.clear()
        for ch in self.channels.values():
            self.add_channel_to_plot(ch)
            for p in ch.pulses:
                self.add_pulse_to_plot(p)

    @Slot(Sequence)
    def display_simulation(self, sim_seq: Sequence):
        self._displayed_sequence = sim_seq

        # Update the solid waveforms using the simulated math
        for channel in sim_seq.channels.values():
            self.update_channel_waveform(channel)

        # Lookup dictionary of the simulated pulses
        sim_pulses = {}
        for ch in sim_seq.channels.values():
            for p in ch.pulses:
                sim_pulses[p.uid] = p

        # Move the transparent drag regions to match!
        for region in self._pulse_regions:
            sim_p = sim_pulses.get(region.pulse.uid)
            if sim_p:
                region.blockSignals(True)
                region.setRegion([sim_p.start, sim_p.end])
                region.blockSignals(False)

    def clear(self):
        self.plot.clear()
        self._pulse_regions.clear()
        self._channel_visuals.clear()

        self.plot.setLabel("bottom", "Time", units="ns")
        self.plot.setLabel("left", "Channels")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        view_box = self.plot.getViewBox()
        view_box.setLimits(xMin=0, xMax=None)
