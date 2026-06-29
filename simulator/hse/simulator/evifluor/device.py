# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

from enum import IntEnum
import json

from hse.simulator.base import Error, SimulationBase, ValueType


class EviFluorIndex(IntEnum):
    LAST_MEASUREMENT_COUNT = 10
    AUTOGAIN_DELTA = 11
    CUVETTE_EMPTY_DELTA = 12
    CUVETTE_EMPTY_LED_POWER = 14
    CURRENT_LED470_POWER = 15
    CURRENT_LED470_POWER_MIN = 16
    CURRENT_LED470_POWER_MAX = 17
    CURRENT_LED625_POWER = 18
    CURRENT_LED625_POWER_MIN = 19
    CURRENT_LED625_POWER_MAX = 20


class EviFluorStatusLed(IntEnum):
    OFF = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    WHITE = 4


class EviFluorSimulation(SimulationBase):
    def __init__(self, no_air=False):
        super().__init__()
        self._initial_no_air = no_air
        self.reset_state()

    def reset_state(self):
        super().reset_state()
        self.last_measurement_count = 0
        self.last_measurements = []
        self.current_led470_power = 80
        self.current_led625_power = 64
        self.current_led470_power_max = 200
        self.no_air = self._initial_no_air
        self.measure_always_zero = False

    def append_measurement_data(self, data):
        self._data.append(
            f'M {data["dark"]} {data["value"]} {int(data["ledPower"])} '
            f'{self.random_number(21, 34)} {self.random_number(500, 2500)} {self.current_led625_power}'
        )

    def load_data(self, data_file):
        first_air = True
        with open(data_file, "rb") as handle:
            data = json.load(handle)
            for measurement in data["measurements"]:
                if "values" in measurement:
                    for value in measurement["values"]:
                        self.append_measurement_data(value)
                if self.no_air is False and "air" in measurement:
                    self.append_measurement_data(measurement["air"])
                    if first_air:
                        self.append_measurement_data(measurement["air"])
                        first_air = False
                if "sample" in measurement:
                    self.append_measurement_data(measurement["sample"])

    def device_name(self):
        return "eviFluor"

    def handle_control_command(self, args) -> str:
        if len(args) == 2 and args[1] == "RESET":
            response = super().handle_control_command(args)
            self.no_air = False
            return response
        if len(args) == 3 and args[1] == "NO_AIR":
            if args[2] not in ["0", "1"]:
                return f"E {Error.EVI_INVALID_PARAMETER}"
            self.no_air = bool(int(args[2]))
            return "! 0"
        return super().handle_control_command(args)

    def next_measurement_response(self):
        if len(self._data) > 0:
            value = self._data.pop(0)
        else:
            value = (
                f"M {self.random_number(3, 4)} {self.random_number(12, 16)} {self.current_led470_power} "
                f"{self.random_number(21, 34)} {self.random_number(500, 2500)} {self.current_led625_power}"
            )
        self.add_logging_message(f"fake logging message {value}")
        return value

    def handle_measure_command(self, args) -> str:
        if len(args) == 1:
            value = self.next_measurement_response()
            self.last_measurement_count += 1
            self.last_measurements.insert(0, value)

            if len(self.last_measurements) > 20:
                del self.last_measurements[-1]

            return value
        if len(args) == 2:
            return self.last_measurements[int(args[1])]
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_autogain_command(self, args) -> str:
        if len(args) == 2:
            return f"C 1 {self.current_led470_power_max}"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_baseline_command(self, args) -> str:
        if len(args) == 1:
            self.last_measurement_count = 0
            return "G"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_status_led_command(self, args) -> str:
        if len(args) == 2:
            color = int(args[1])
            if color in [
                EviFluorStatusLed.OFF,
                EviFluorStatusLed.RED,
                EviFluorStatusLed.GREEN,
                EviFluorStatusLed.BLUE,
                EviFluorStatusLed.WHITE,
            ]:
                return "Z"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_command(self, args) -> str:
        if args[0] == "G":
            return self.handle_baseline_command(args)
        if args[0] == "M":
            return self.handle_measure_command(args)
        if args[0] == "C":
            return self.handle_autogain_command(args)
        if args[0] == "Z":
            return self.handle_status_led_command(args)
        return super().handle_command(args)

    def set_value_command(self, index, value):
        if index == EviFluorIndex.CURRENT_LED470_POWER:
            self.current_led470_power = value
            return "V"
        if index == EviFluorIndex.CURRENT_LED625_POWER:
            self.current_led625_power = value
            return "V"
        return super().set_value_command(index, value)

    def get_value_command(self, index):
        if index == EviFluorIndex.LAST_MEASUREMENT_COUNT:
            return f"V {self.last_measurement_count}"
        if index == EviFluorIndex.AUTOGAIN_DELTA:
            return "V 0"
        if index == EviFluorIndex.CUVETTE_EMPTY_DELTA:
            return "V 0"
        if index == EviFluorIndex.CUVETTE_EMPTY_LED_POWER:
            return "V 0"
        if index == EviFluorIndex.CURRENT_LED470_POWER:
            return f"V {self.current_led470_power}"
        if index == EviFluorIndex.CURRENT_LED470_POWER_MIN:
            return "V 30"
        if index == EviFluorIndex.CURRENT_LED470_POWER_MAX:
            return f"V {self.current_led470_power_max}"
        if index == EviFluorIndex.CURRENT_LED625_POWER:
            return f"V {self.current_led625_power}"
        if index == EviFluorIndex.CURRENT_LED625_POWER_MIN:
            return "V 0"
        if index == EviFluorIndex.CURRENT_LED625_POWER_MAX:
            return "V 0"
        return super().get_value_command(index)

    def get_value_type_command(self, index) -> str:
        if index in [
            EviFluorIndex.LAST_MEASUREMENT_COUNT,
            EviFluorIndex.AUTOGAIN_DELTA,
            EviFluorIndex.CUVETTE_EMPTY_DELTA,
            EviFluorIndex.CUVETTE_EMPTY_LED_POWER,
            EviFluorIndex.CURRENT_LED470_POWER,
            EviFluorIndex.CURRENT_LED470_POWER_MIN,
            EviFluorIndex.CURRENT_LED470_POWER_MAX,
            EviFluorIndex.CURRENT_LED625_POWER,
            EviFluorIndex.CURRENT_LED625_POWER_MIN,
            EviFluorIndex.CURRENT_LED625_POWER_MAX,
        ]:
            return f"H {ValueType.UINT32}"
        return super().get_value_type_command(index)

    # Backward-compatible wrappers
    def append_data(self, data):
        self.append_measurement_data(data)

    def measure(self):
        return self.next_measurement_response()

    def commandM_measure(self, args) -> str:
        return self.handle_measure_command(args)

    def commandC_autogain(self, args) -> str:
        return self.handle_autogain_command(args)

    def commandG_baseline(self, args) -> str:
        return self.handle_baseline_command(args)

    def commandZ_statusLED(self, args) -> str:
        return self.handle_status_led_command(args)

    def commandV_ValueSet(self, index, value):
        return self.set_value_command(index, value)

    def commandV_ValueGet(self, index):
        return self.get_value_command(index)

    def commandH_typeOf(self, index) -> str:
        return self.get_value_type_command(index)

    def command_simulator(self, args) -> str:
        return self.handle_control_command(args)


# Backward-compatible aliases
IndexEviFluor = EviFluorIndex
StatusLedEviFluor = EviFluorStatusLed
simulation_evifluor = EviFluorSimulation
