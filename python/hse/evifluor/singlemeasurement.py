# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from hse.evifluor.channel import Channel


class SingleMeasurement:
    """Represents a single measurement consisting of the 470 nm wavelength channel."""

    def __init__(self, channel_470 = Channel()):
        """Initializes the measurement with an optional 470 nm channel."""
        self.channel_470 = channel_470
        
    def __repr__(self):
        """Returns a compact textual representation of the measurement."""
        return "470: [{}]".format(self.channel_470)
        
    def to_json(self):
        """Converts the measurement data to a JSON representation."""
        return self.channel_470.to_json()
        
    def delta(self):
        """Returns the difference between sample signal and dark signal."""
        return self.channel_470.delta()
               
    @staticmethod
    def from_json(node):
        """Creates a SingleMeasurement instance from a JSON node."""
        return SingleMeasurement(Channel.from_json(node))
