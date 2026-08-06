import copy
import math
import uuid
from dataclasses import dataclass, field
from typing import Literal

CHANNEL_COLOR_PALLETTE = {
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "apd": (214, 32, 81),
    "default": (0, 150, 255),
}


@dataclass
class Pulse:
    """Holds the raw physical parameters of an individual pulse element."""

    start: int  # in ns
    duration: int  # in ns
    channel: object
    comment: str = ""
    start_sweep: str = ""
    duration_sweep: str = ""
    ripple: Literal["none", "channel", "global"] = "none"
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def end(self) -> int:  # in ns
        return self.start + self.duration

    def move_to_channel(self, new_channel: object):

        if self.channel == new_channel:
            return  # No change needed

        if self in self.channel.pulses:
            self.channel.pulses.remove(self)

        self.channel = new_channel
        new_channel.pulses.append(self)

@dataclass
class Channel:
    name: str
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    pulses: list = field(default_factory=list)
    pb_id: int = 0
    delay: tuple = (0.0, 0.0)
    color: tuple = (0, 150, 255)

    def add_pulse(self, start: int, duration: int) -> Pulse:
        # Enforce chronological ordering or prevent overlaps here if needed
        p = Pulse(start, duration, channel=self)
        self.pulses.append(p)
        return p

    def remove_pulse(self, pulse: Pulse):
        self.pulses.remove(pulse)


@dataclass
class Sequence:
    channels: dict = field(default_factory=dict)
    pulses: list = field(default_factory=list)
    iterations: int = 100
    name: str = "Unnamed"

    def add_channel(self, channel: Channel):
        self.channels[channel.uid] = channel

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

    def get_channel_span(self, channel_uid: str) -> tuple:
        lane_idx = self.get_channel_lane_index(channel_uid)

        span = (lane_idx, lane_idx + 1)
        return span

    def get_channel(self, name: str) -> Channel:
        return self.channels.get(name, None)

    def get_pulse(self, pulse_uid: str) -> Pulse:
        for pulse in self.pulses:
            if pulse.uid == pulse_uid:
                return pulse
        return None

    def add_pulse(self, pulse: Pulse):
        self.pulses.append(pulse)

    # -------------------------------------------------------------------------
    # Sequence compiler
    # -------------------------------------------------------------------------
    def evaluate_iteration(self, i: int, apply_delay: bool = False) -> "Sequence":

        # Deepcopy so we don't ruin the original sequence!
        sim_seq = copy.deepcopy(self)

        # Prepare the math variables allowed in the UI
        env = {"i": i, "math": math}

        # Track ripple offsets
        global_ripple = 0
        channel_ripples = {ch.uid: 0 for ch in sim_seq.channels.values()}

        # Sort all pulses chronologically so rippling works left-to-right
        all_pulses = []
        for ch in sim_seq.channels.values():
            all_pulses.extend(ch.pulses)
        all_pulses.sort(key=lambda p: p.start)

        # Evaluate sweeps
        for pulse in all_pulses:
            env["S"] = pulse.start
            env["W"] = pulse.duration

            delta_start = 0
            if pulse.start_sweep:
                try:
                    new_start = int(
                        eval(pulse.start_sweep, {"__builtins__": None}, env)
                    )
                    delta_start = new_start - pulse.start
                except Exception:
                    pass  # Ignore bad math while typing

            delta_width = 0
            if pulse.duration_sweep:
                try:
                    new_width = int(
                        eval(pulse.duration_sweep, {"__builtins__": None}, env)
                    )
                    delta_width = new_width - pulse.duration
                except Exception:
                    pass

            # Apply the evaluated math + accumulated ripples
            pulse.start += (
                delta_start + global_ripple + channel_ripples[pulse.channel.uid]
            )
            pulse.duration += delta_width

            # Add this pulse's movement to the ripple trackers for subsequent pulses
            if pulse.ripple == "global":
                global_ripple += delta_start + delta_width
            elif pulse.ripple == "channel":
                channel_ripples[pulse.channel.uid] += delta_start + delta_width

        if not apply_delay:
            return sim_seq

        for pulse in all_pulses:
            delay_on, delay_off = pulse.channel.delay

            ttl_start = pulse.start - int(delay_on)
            ttl_end = pulse.start + pulse.duration - int(delay_off)

            pulse.start = max(0, ttl_start)
            pulse.duration = max(0, ttl_end - pulse.start)

        return sim_seq

    @property
    def duration(self) -> int:
        max_end = 0
        for channel in self.channels.values():
            for pulse in channel.pulses:
                if pulse.end > max_end:
                    max_end = pulse.end

        return max_end

    @property
    def detector_pulses(self) -> int:
        detector_pulses = 0
        for channel in self.channels.values():
            if "APD" in channel.name.upper():
                detector_pulses = len(channel.pulses)

        return detector_pulses

    def evaluate_all(self, num_iterations: int) -> list:
        """Evaluate the sequence for a given number of iterations and returns them in a list."""
        return [self.evaluate_iteration(i) for i in range(len(num_iterations))]

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self):
        return {
            "name": self.name,
            "iterations": self.iterations,
            "channels": [
                {
                    "name": ch.name,
                    "pb_id": ch.pb_id,
                    "color": list(ch.color),
                    "delay": list(ch.delay),
                    "pulses": [
                        {
                            "start": p.start,
                            "duration": p.duration,
                            "comment": p.comment,
                            "start_sweep": p.start_sweep,
                            "duration_sweep": p.duration_sweep,
                            "ripple": p.ripple,
                        }
                        for p in ch.pulses
                    ],
                }
                for ch in self.channels.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Sequence":
        seq = cls()
        seq.iterations = data.get("iterations", 100)
        seq.name = data.get("name", "Unnamed")
        for ch_data in data.get("channels", []):
            channel = Channel(
                name=ch_data.get("name", "unnamed"),
                pb_id=ch_data.get("pb_id", 0),
                color=tuple(ch_data.get("color", [0, 150, 255])),
                delay=tuple(ch_data.get("delay", [0.0, 0.0]))
            )
            for p_data in ch_data.get("pulses", []):
                pulse = Pulse(
                    start=p_data["start"],
                    duration=p_data["duration"],
                    channel=channel,
                    comment=p_data.get("comment", ""),
                    start_sweep=p_data.get("start_sweep", ""),
                    duration_sweep=p_data.get("duration_sweep", ""),
                    ripple=p_data.get("ripple", "none"),
                )
                channel.pulses.append(pulse)
            seq.add_channel(channel)
        return seq


