# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from hse.evifluor.constants import DictKeys


class Channel:
    """Represents a measurement channel with sample and reference values, measured in mV."""

    def __init__(self, dark = 0.0, value = 0.0, led_power = 0.0):
        """Initializes a new Channel with optional dark/value values and LED power."""
        self.dark      = dark
        self.value     = value
        self.led_power = led_power
        
    def __repr__(self):
        """Returns a string representation of the channel values."""
        return "dark:{} value:{} led_power:{}".format(self.dark, self.value, self.led_power)
        
    def delta(self):
        """Calculates the difference between illuminated value and dark signal."""
        return self.value - self.dark

    def to_json(self):
        """Converts the channel values to a JSON representation."""
        return {
            DictKeys.DARK: self.dark,
            DictKeys.VALUE: self.value,
            DictKeys.LED_POWER: self.led_power,
        }
     
    @staticmethod
    def from_json(node):
        """Creates a Channel instance from a JSON node."""
        return Channel(
            node[DictKeys.DARK],
            node[DictKeys.VALUE],
            node[DictKeys.LED_POWER],
        )
