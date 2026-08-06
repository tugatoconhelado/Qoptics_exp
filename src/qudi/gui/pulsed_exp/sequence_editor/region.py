import pyqtgraph as pg
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QGraphicsItem

from .structures import Channel, Pulse

HARDWARE_CLOCK_TICK_NS = 2


class PulseRegionItem(pg.LinearRegionItem):
    """
    An invisible/transparent interactive layer that acts as the mouse handle.
    It synchronizes its width back to the data model and updates the step trace.
    """

    sig_pulse_moved = Signal(Channel, Pulse)
    pulse_selected_sig = Signal(Pulse)
    delete_requested_sig = Signal(Pulse)

    def __init__(
        self, pulse_model: Pulse, channel_model: Channel, plot_canvas, lane_idx=1
    ):
        super().__init__(
            values=[pulse_model.start, pulse_model.end],
            orientation=pg.LinearRegionItem.Vertical,
            swapMode="block",
        )
        self.pulse: Pulse = pulse_model
        self.channel: Channel = channel_model
        self.plot_canvas = plot_canvas
        self.lane_idx = lane_idx

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

        # Transparent background for mouse interaction only
        r, g, b = self.channel.color
        self.setBrush(pg.mkBrush(r, g, b, 30))
        self.setHoverBrush(pg.mkBrush(r, g, b, 70))

        side_pen = pg.mkPen(color=(r, g, b, 100), width=1, style=Qt.PenStyle.DashLine)
        hover_pen = pg.mkPen(color=(r, g, b, 255), width=2, style=Qt.PenStyle.SolidLine)
        for line in self.lines:
            line.setPen(side_pen)
            line.setHoverPen(hover_pen)

        self.sigRegionChanged.connect(self.handle_geometry_changes)

        # Bind vertical span sync safely without attachedToPlot
        view_box = self.plot_canvas.getViewBox()
        view_box.sigYRangeChanged.connect(self.sync_vertical_span)
        self.sync_vertical_span()

    def hoverEvent(self, ev):
        if ev.isExit():
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        super().hoverEvent(ev)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pulse_selected_sig.emit(self.pulse)
        super().mouseClickEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_requested_sig.emit(self.pulse)
            ev.accept()
        else:
            super().keyPressEvent(ev)

    def sync_vertical_span(self):
        view_box = self.plot_canvas.getViewBox()
        if not view_box:
            return
        y_min, y_max = view_box.viewRange()[1]
        total_range = y_max - y_min
        if total_range == 0:
            return

        lane_bottom = self.lane_idx + 0.1
        lane_top = self.lane_idx + 0.9

        for line in self.lines:
            line.prepareGeometryChange()

        self.setSpan(
            *((lane_bottom - y_min) / total_range, (lane_top - y_min) / total_range)
        )

    def handle_geometry_changes(self):
        left, right = self.getRegion()
        snapped_left = max(
            0, round(left / HARDWARE_CLOCK_TICK_NS) * HARDWARE_CLOCK_TICK_NS
        )
        snapped_right = max(
            snapped_left + HARDWARE_CLOCK_TICK_NS,
            round(right / HARDWARE_CLOCK_TICK_NS) * HARDWARE_CLOCK_TICK_NS,
        )

        self.blockSignals(True)
        self.setRegion([snapped_left, snapped_right])
        self.blockSignals(False)

        self.pulse.start = snapped_left
        self.pulse.duration = snapped_right - snapped_left

        # Tell the main app to redraw the solid line
        self.sig_pulse_moved.emit(self.channel, self.pulse)

        self.pulse_selected_sig.emit(self.pulse)

    def update_region(self, pulse: Pulse, lane_idx: int = None):
        """Update the visual representation of the pulse region based on the data model."""
        if self.channel != pulse.channel:
            new_channel = pulse.channel
            self.prepareGeometryChange()

            if lane_idx is not None:
                self.lane_idx = lane_idx

            self.channel = new_channel

            r, g, b = new_channel.color
            self.setBrush(pg.mkBrush(r, g, b, 30))
            self.setHoverBrush(pg.mkBrush(r, g, b, 70))

            side_pen = pg.mkPen(
                color=(r, g, b, 100), width=1, style=Qt.PenStyle.DashLine
            )
            hover_pen = pg.mkPen(
                color=(r, g, b, 255), width=2, style=Qt.PenStyle.SolidLine
            )
            for line in self.lines:
                line.setPen(side_pen)
                line.setHoverPen(hover_pen)

            self.sync_vertical_span()

            if self.plot_canvas and self.plot_canvas.scene():
                self.plot_canvas.scene().update()

        self.blockSignals(True)
        self.setRegion([pulse.start, pulse.end])
        self.blockSignals(False)
