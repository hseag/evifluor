# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from hse.evifluor.channel import Channel


class SingleMeasurement:
    """Represents a single measurement consisting of the 470 nm wavelength channel."""

    def __init__(self, channel_470 = Channel()):
        """Initializes a single measurement.

        Args:
            channel_470: Channel data for the 470 nm measurement channel. Defaults
                to a new empty :class:`Channel`.
        """
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
        """Creates a single measurement from a JSON node.

        Args:
            node: JSON object containing the serialized 470 nm channel data.

        Returns:
            A new :class:`SingleMeasurement` instance.
        """
        return SingleMeasurement(Channel.from_json(node))
