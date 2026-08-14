# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

from enum import IntEnum
import json

from hse.simulator.base import Error, SimulationBase, ValueType


class EviDenseIndex(IntEnum):
    LAST_MEASUREMENT_COUNT = 10
    LED230NM_MAX_CURRENT = 23
    LED260NM_MAX_CURRENT = 33
    LED280NM_MAX_CURRENT = 43
    LED340NM_MAX_CURRENT = 53
    SELFTEST_AMPLIFIER_SPLITRATIO230NM = 100
    SELFTEST_AMPLIFIER_CURRENT = 101
    SELFTEST_AMPLIFIER_SAMPLE1 = 102
    SELFTEST_AMPLIFIER_SAMPLE11 = 103
    SELFTEST_AMPLIFIER_SAMPLE111 = 104
    SELFTEST_AMPLIFIER_REFERENCE1 = 105
    SELFTEST_AMPLIFIER_REFERENCE11 = 106
    SELFTEST_AMPLIFIER_REFERENCE111 = 107
    SELFTEST_AMPLIFIER_SETUPRESULT = 108
    SELFTEST_LED230_ILED = 110
    SELFTEST_LED230_DARKSAMPLE = 111
    SELFTEST_LED230_DARKREFERENCE = 112
    SELFTEST_LED230_SAMPLE = 113
    SELFTEST_LED230_REFERENCE = 114
    SELFTEST_LED260_ILED = 120
    SELFTEST_LED260_DARKSAMPLE = 121
    SELFTEST_LED260_DARKREFERENCE = 122
    SELFTEST_LED260_SAMPLE = 123
    SELFTEST_LED260_REFERENCE = 124
    SELFTEST_LED280_ILED = 130
    SELFTEST_LED280_DARKSAMPLE = 131
    SELFTEST_LED280_DARKREFERENCE = 132
    SELFTEST_LED280_SAMPLE = 133
    SELFTEST_LED280_REFERENCE = 134
    SELFTEST_LED340_ILED = 140
    SELFTEST_LED340_DARKSAMPLE = 141
    SELFTEST_LED340_DARKREFERENCE = 142
    SELFTEST_LED340_SAMPLE = 143
    SELFTEST_LED340_REFERENCE = 144
    LEVELLING_LED230_SETUPRESULT = 150
    LEVELLING_LED230_CURRENT = 151
    LEVELLING_LED230_AMPLIFICATIONSAMPLE = 152
    LEVELLING_LED230_AMPLIFICATIONREFERENCE = 153
    LEVELLING_LED260_SETUPRESULT = 160
    LEVELLING_LED260_CURRENT = 161
    LEVELLING_LED260_AMPLIFICATIONSAMPLE = 162
    LEVELLING_LED260_AMPLIFICATIONREFERENCE = 163
    LEVELLING_LED280_SETUPRESULT = 170
    LEVELLING_LED280_CURRENT = 171
    LEVELLING_LED280_AMPLIFICATIONSAMPLE = 172
    LEVELLING_LED280_AMPLIFICATIONREFERENCE = 173
    LEVELLING_LED340_SETUPRESULT = 180
    LEVELLING_LED340_CURRENT = 181
    LEVELLING_LED340_AMPLIFICATIONSAMPLE = 182
    LEVELLING_LED340_AMPLIFICATIONREFERENCE = 183


class EviDenseStatusLed(IntEnum):
    OFF = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class EviDenseLed(IntEnum):
    NONE = 0
    LED_230NM = 1
    LED_260NM = 2
    LED_280NM = 3
    LED_340NM = 4


class EviDenseSimulation(SimulationBase):
    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        super().reset_state()
        self.last_measurement_count = 0
        self.last_measurements = []
        self.last_levelling = "C 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
        self.current = 0
        self.led = 0
        self.amplifiers = [0, 0, 0]
        self.center_wavelengths = {"230": 230000, "260": 260000, "280": 280000, "340": 340000}
        self.measure_always_zero = False

    def device_name(self):
        return "eviDense"

    def format_measurement_pair(self, led):
        return f"{led['sample']} {led['reference']}"

    def append_measurement_data(self, data):
        self._data.append(
            f"M {self.format_measurement_pair(data['230'])} {self.format_measurement_pair(data['260'])} "
            f"{self.format_measurement_pair(data['280'])} {self.format_measurement_pair(data['340'])}"
        )

    def load_data(self, data_file):
        with open(data_file, "rb") as handle:
            data = json.load(handle)
            for measurement in data["measurements"]:
                if "baseline" in measurement:
                    self.append_measurement_data(measurement["baseline"])
                if "air" in measurement:
                    self.append_measurement_data(measurement["air"])
                if "sample" in measurement:
                    self.append_measurement_data(measurement["sample"])

        adjustments = data.get("adjustments", {})
        center_wavelengths = adjustments.get("centerwavelengths", {})
        for channel in ["230", "260", "280", "340"]:
            if channel in center_wavelengths:
                self.center_wavelengths[channel] = int(center_wavelengths[channel] * 1000.0)

    def handle_command(self, args) -> str:
        if args[0] == "G":
            return self.handle_baseline_command(args)
        if args[0] == "M":
            return self.handle_measure_command(args)
        if args[0] == "C":
            return self.handle_levelling_command(args)
        if args[0] == "Z":
            return self.handle_status_led_command(args)
        if args[0] == "L":
            return self.handle_set_led_current_command(args)
        if args[0] == "D":
            return self.handle_set_detector_amplifying_command(args)
        if args[0] == "A":
            return self.handle_auto_update_command(args)
        return super().handle_command(args)

    def get_value_command(self, index):
        if index == EviDenseIndex.LAST_MEASUREMENT_COUNT:
            return f"V {self.last_measurement_count}"
        if index == EviDenseIndex.LED230NM_MAX_CURRENT:
            return "V 200000"
        if index in [EviDenseIndex.LED260NM_MAX_CURRENT, EviDenseIndex.LED280NM_MAX_CURRENT]:
            return "V 150000"
        if index == EviDenseIndex.LED340NM_MAX_CURRENT:
            return "V 220000"
        if index in [
            EviDenseIndex.SELFTEST_AMPLIFIER_SPLITRATIO230NM,
            EviDenseIndex.SELFTEST_AMPLIFIER_CURRENT,
            EviDenseIndex.SELFTEST_AMPLIFIER_SAMPLE1,
            EviDenseIndex.SELFTEST_AMPLIFIER_SAMPLE11,
            EviDenseIndex.SELFTEST_AMPLIFIER_SAMPLE111,
            EviDenseIndex.SELFTEST_AMPLIFIER_REFERENCE1,
            EviDenseIndex.SELFTEST_AMPLIFIER_REFERENCE11,
            EviDenseIndex.SELFTEST_AMPLIFIER_REFERENCE111,
            EviDenseIndex.SELFTEST_AMPLIFIER_SETUPRESULT,
            EviDenseIndex.SELFTEST_LED230_ILED,
            EviDenseIndex.SELFTEST_LED230_DARKSAMPLE,
            EviDenseIndex.SELFTEST_LED230_DARKREFERENCE,
            EviDenseIndex.SELFTEST_LED230_SAMPLE,
            EviDenseIndex.SELFTEST_LED230_REFERENCE,
            EviDenseIndex.SELFTEST_LED260_ILED,
            EviDenseIndex.SELFTEST_LED260_DARKSAMPLE,
            EviDenseIndex.SELFTEST_LED260_DARKREFERENCE,
            EviDenseIndex.SELFTEST_LED260_SAMPLE,
            EviDenseIndex.SELFTEST_LED260_REFERENCE,
            EviDenseIndex.SELFTEST_LED280_ILED,
            EviDenseIndex.SELFTEST_LED280_DARKSAMPLE,
            EviDenseIndex.SELFTEST_LED280_DARKREFERENCE,
            EviDenseIndex.SELFTEST_LED280_SAMPLE,
            EviDenseIndex.SELFTEST_LED280_REFERENCE,
            EviDenseIndex.SELFTEST_LED340_ILED,
            EviDenseIndex.SELFTEST_LED340_DARKSAMPLE,
            EviDenseIndex.SELFTEST_LED340_DARKREFERENCE,
            EviDenseIndex.SELFTEST_LED340_SAMPLE,
            EviDenseIndex.SELFTEST_LED340_REFERENCE,
            EviDenseIndex.LEVELLING_LED230_SETUPRESULT,
            EviDenseIndex.LEVELLING_LED230_CURRENT,
            EviDenseIndex.LEVELLING_LED230_AMPLIFICATIONSAMPLE,
            EviDenseIndex.LEVELLING_LED230_AMPLIFICATIONREFERENCE,
            EviDenseIndex.LEVELLING_LED260_SETUPRESULT,
            EviDenseIndex.LEVELLING_LED260_CURRENT,
            EviDenseIndex.LEVELLING_LED260_AMPLIFICATIONSAMPLE,
            EviDenseIndex.LEVELLING_LED260_AMPLIFICATIONREFERENCE,
            EviDenseIndex.LEVELLING_LED280_SETUPRESULT,
            EviDenseIndex.LEVELLING_LED280_CURRENT,
            EviDenseIndex.LEVELLING_LED280_AMPLIFICATIONSAMPLE,
            EviDenseIndex.LEVELLING_LED280_AMPLIFICATIONREFERENCE,
            EviDenseIndex.LEVELLING_LED340_SETUPRESULT,
            EviDenseIndex.LEVELLING_LED340_CURRENT,
            EviDenseIndex.LEVELLING_LED340_AMPLIFICATIONSAMPLE,
            EviDenseIndex.LEVELLING_LED340_AMPLIFICATIONREFERENCE,
        ]:
            return "V 0"
        if index == 24:
            return f"V {self.center_wavelengths['230']}"
        if index == 34:
            return f"V {self.center_wavelengths['260']}"
        if index == 44:
            return f"V {self.center_wavelengths['280']}"
        if index == 54:
            return f"V {self.center_wavelengths['340']}"
        return super().get_value_command(index)

    def get_value_type_command(self, index) -> str:
        supported = {member.value for member in EviDenseIndex}
        supported.update([24, 34, 44, 54])
        if index in supported:
            return f"H {ValueType.UINT32}"
        return super().get_value_type_command(index)

    def next_measurement_response(self, command):
        if self.measure_always_zero:
            return f"{command} 0 0 0 0 0 0 0 0"
        if len(self._data) > 0:
            value = self._data.pop(0)
            value = command + value[1:]
        else:
            sample_delta = 2000
            sample_target = 4500000
            reference_delta = 2000
            reference_target = 3500000
            value = (
                f"{command} "
                f"{self.random_number_as_int(sample_target - sample_delta, sample_target + sample_delta)} "
                f"{self.random_number_as_int(reference_target - reference_delta, reference_target + reference_delta)} "
                f"{self.random_number_as_int(sample_target - sample_delta, sample_target + sample_delta)} "
                f"{self.random_number_as_int(reference_target - reference_delta, reference_target + reference_delta)} "
                f"{self.random_number_as_int(sample_target - sample_delta, sample_target + sample_delta)} "
                f"{self.random_number_as_int(reference_target - reference_delta, reference_target + reference_delta)} "
                f"{self.random_number_as_int(sample_target - sample_delta, sample_target + sample_delta)} "
                f"{self.random_number_as_int(reference_target - reference_delta, reference_target + reference_delta)}"
            )
        self.add_logging_message(f"fake logging message {value}")
        return value

    def handle_baseline_command(self, args) -> str:
        if len(args) == 1:
            self.last_measurement_count = 0
            value = self.next_measurement_response("G")
            self.last_measurement_count += 1
            self.last_measurements.insert(0, "M" + value[1:])

            if len(self.last_measurements) > 20:
                del self.last_measurements[-1]

            return value
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_measure_command(self, args) -> str:
        if len(args) == 1:
            value = self.next_measurement_response("M")
            self.last_measurement_count += 1
            if len(self.last_measurements) > 20:
                del self.last_measurements[-1]
            else:
                self.last_measurements.insert(0, value)
            return value
        if len(args) == 2:
            return self.last_measurements[int(args[1])]
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_levelling_command(self, args) -> str:
        if len(args) == 1:
            self.last_levelling = (
                f"C 0 {self.random_number_as_int(1000, 60000)} 0 0 0 {self.random_number_as_int(1000, 60000)} "
                f"0 0 0 {self.random_number_as_int(1000, 60000)} 0 0 0 {self.random_number_as_int(1000, 60000)} 0 0"
            )
            self.add_logging_message(f"fake logging message {self.last_levelling}")
            return self.last_levelling
        if len(args) == 2:
            return self.last_levelling
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_status_led_command(self, args) -> str:
        if len(args) == 2:
            color = int(args[1])
            if color in [EviDenseStatusLed.OFF, EviDenseStatusLed.RED, EviDenseStatusLed.GREEN, EviDenseStatusLed.BLUE]:
                return "Z"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_set_led_current_command(self, args) -> str:
        if len(args) == 3:
            self.led = EviDenseLed(int(args[1]))
            self.current = int(args[2])
            return "L"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_set_detector_amplifying_command(self, args) -> str:
        if len(args) == 3:
            self.amplifiers[int(args[1])] = int(args[2])
            return "D"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def voltage(self, factor, amplifier_index) -> int:
        if self.led == EviDenseLed.NONE:
            return 0
        gains = [1.1, 11, 111]
        value = (self.current * factor + 1000) * gains[self.amplifiers[amplifier_index]]
        return int(min(value, 5000000))

    def handle_auto_update_command(self, args) -> str:
        if len(args) == 2:
            return "A"
        if len(args) == 1:
            return f"A {self.voltage(0.321, 0)} {self.voltage(0.123, 1)} 5000000 {self.current}"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    # Backward-compatible wrappers
    def toMeasurement(self, led):
        return self.format_measurement_pair(led)

    def append_data(self, data):
        self.append_measurement_data(data)

    def measure(self, command):
        return self.next_measurement_response(command)

    def commandV_ValueGet(self, index):
        return self.get_value_command(index)

    def commandH_typeOf(self, index) -> str:
        return self.get_value_type_command(index)

    def commandG_baseline(self, args) -> str:
        return self.handle_baseline_command(args)

    def commandM_measure(self, args) -> str:
        return self.handle_measure_command(args)

    def commandC_levelling(self, args) -> str:
        return self.handle_levelling_command(args)

    def commandZ_statusLED(self, args) -> str:
        return self.handle_status_led_command(args)

    def commandL_SetLedCurrent(self, args) -> str:
        return self.handle_set_led_current_command(args)

    def commandD_SetDetectorAmplifiying(self, args) -> str:
        return self.handle_set_detector_amplifying_command(args)

    def commandA_AutoUpdate(self, args) -> str:
        return self.handle_auto_update_command(args)


# Backward-compatible aliases
IndexEviDense = EviDenseIndex
StatusLedEviDense = EviDenseStatusLed
LedEviDense = EviDenseLed
simulation_evidense = EviDenseSimulation
