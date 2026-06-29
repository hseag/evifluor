# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from enum import Enum, Flag

from hse.evifluor.device import (
    AutoGainResult,
    FirstAirMeasurementResult,
    FirstSampleMeasurementResult,
)
from hse.evifluor.measurement import Measurement, Results
from hse.evifluor.singlemeasurement import SingleMeasurement


class Verification:
    """Provides verification checks for various measurement types and conditions."""
    _DEFAULT_STD_HIGH_TARGET_SIGNAL_FACTOR      = 0.8
    _DEFAULT_MIN_RFU                          = 4.5
    _min_rfu                                  = _DEFAULT_MIN_RFU
    _DEFAULT_MAX_RFU                          = 35.0
    _max_rfu                                  = _DEFAULT_MAX_RFU
    _DEFAULT_MIN_LED                          = 32
    _min_led                                  = _DEFAULT_MIN_LED
    _DEFAULT_MAX_LED                          = 222
    _max_led                                  = _DEFAULT_MAX_LED
    _DEFAULT_THRESHOLD_MULTIPLIER             = 2.0
    _threshold_multiplier                     = _DEFAULT_THRESHOLD_MULTIPLIER
    _DEFAULT_MAX_SIGNAL                       = 2499.0
    _max_signal                               = _DEFAULT_MAX_SIGNAL
    _DEFAULT_STD_HIGH_DELTA                   = 300
    _std_high_delta                           = _DEFAULT_STD_HIGH_DELTA
    _DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION = -0.1
    _threshold_negative_concentration         = _DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION

    @staticmethod
    def set_min_rfu(value):
        """Sets the minimum expected RFU value or resets to the default."""
        if value is None:
            Verification._min_rfu = Verification._DEFAULT_MIN_RFU
        else:
            Verification._min_rfu = value

    @property
    def min_rfu(self):
        """Gets the current minimum expected RFU value."""
        return Verification._min_rfu

    @min_rfu.setter
    def min_rfu(self, value):
        """Sets the current minimum expected RFU value."""
        Verification.set_min_rfu(value)

    @staticmethod
    def set_max_rfu(value):
        """Sets the maximum expected RFU value or resets to the default."""
        if value is None:
            Verification._max_rfu = Verification._DEFAULT_MAX_RFU
        else:
            Verification._max_rfu = value

    @property
    def max_rfu(self):
        """Gets the current maximum expected RFU value."""
        return Verification._max_rfu

    @max_rfu.setter
    def max_rfu(self, value):
        """Sets the current maximum expected RFU value."""
        Verification.set_max_rfu(value)

    @staticmethod
    def set_min_led(value):
        """Sets the minimum expected LED power or resets to the default."""
        if value is None:
            Verification._min_led = Verification._DEFAULT_MIN_LED
        else:
            Verification._min_led = value

    @property
    def min_led(self):
        """Gets the current minimum expected LED power."""
        return Verification._min_led

    @min_led.setter
    def min_led(self, value):
        """Sets the current minimum expected LED power."""
        Verification.set_min_led(value)

    @staticmethod
    def set_max_led(value):
        """Sets the maximum expected LED power or resets to the default."""
        if value is None:
            Verification._max_led = Verification._DEFAULT_MAX_LED
        else:
            Verification._max_led = value

    @property
    def max_led(self):
        """Gets the current maximum expected LED power."""
        return Verification._max_led

    @max_led.setter
    def max_led(self, value):
        """Sets the current maximum expected LED power."""
        Verification.set_max_led(value)

    @staticmethod
    def set_threshold_multiplier(value):
        """Sets the RFU threshold multiplier used when detecting cuvette presence."""
        if value is None:
            Verification._threshold_multiplier = Verification._DEFAULT_THRESHOLD_MULTIPLIER
        else:
            Verification._threshold_multiplier = value

    @property
    def threshold_multiplier(self):
        """Gets the RFU threshold multiplier used when detecting cuvette presence."""
        return Verification._threshold_multiplier

    @threshold_multiplier.setter
    def threshold_multiplier(self, value):
        """Sets the RFU threshold multiplier used when detecting cuvette presence."""
        Verification.set_threshold_multiplier(value)

    @staticmethod
    def set_max_signal(value):
        """Sets the maximum allowed signal value before saturation."""
        if value is None:
            Verification._max_signal = Verification._DEFAULT_MAX_SIGNAL
        else:
            Verification._max_signal = value

    @property
    def max_signal(self):
        """Gets the maximum allowed signal value before saturation."""
        return Verification._max_signal

    @max_signal.setter
    def max_signal(self, value):
        """Sets the maximum allowed signal value before saturation."""
        Verification.set_max_signal(value)

    @staticmethod
    def set_std_high_delta(value):
        """Sets the allowed deviation around the standard high target."""
        if value is None:
            Verification._std_high_delta = Verification._DEFAULT_STD_HIGH_DELTA
        else:
            Verification._std_high_delta = value

    @property
    def std_high_delta(self):
        """Gets the allowed deviation around the standard high target."""
        return Verification._std_high_delta

    @std_high_delta.setter
    def std_high_delta(self, value):
        """Sets the allowed deviation around the standard high target."""
        Verification.set_std_high_delta(value)

    @staticmethod
    def set_threshold_negative_concentration(value):
        """Sets the threshold used to flag negative concentrations."""
        if value is None:
            Verification._threshold_negative_concentration = Verification._DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION
        else:
            Verification._threshold_negative_concentration = value

    @property
    def threshold_negative_concentration(self):
        """Gets the threshold used to flag negative concentrations."""
        return Verification._threshold_negative_concentration

    @threshold_negative_concentration.setter
    def threshold_negative_concentration(self, value):
        """Sets the threshold used to flag negative concentrations."""
        Verification.set_threshold_negative_concentration(value)

    class ProblemId(Enum):
        """Problem identifiers tracked during verification."""
        SATURATION             = 1
        CUVETTE_MISSING        = 2
        MIN_LED_POWER          = 3
        MAX_LED_POWER          = 4
        AUTO_GAIN_RESULT       = 5
        WRONG_LEVEL            = 6
        NEGATIVE_CONCENTRATION = 7
    
    class Hints(Flag):
        """Context-sensitive hints that adjust verification checks."""
        NONE                   = 0
        MUST_HAVE_CUVETTE      = 1
        STD_HIGH               = 2

    class Entry:
        def __init__(self, problem_id, data):
            """Initializes a verification entry with the given problem identifier and data."""
            self.problem_id = problem_id
            self.data       = data
    
        def __repr__(self):
            """Returns a readable representation of the entry."""
            return "{}({}) {}".format(self.problem_id.name, self.problem_id.value, self.data)
    
        def to_json(self):
            """Converts the entry to a JSON-friendly dictionary."""
            ret = { 'problem_id'  : self.problem_id.value,
                    'description' : self.problem_id.name}
            if callable(getattr(self.data, "to_json", None)):
                ret['data'] = self.data.to_json()
            else:
                ret['data'] = self.data
            return ret

        @staticmethod
        def from_json(node):
            """Restores a verification entry from JSON data."""
            return Verification.Entry(Verification.ProblemId(node['problem_id']), node['data'])

    def __init__(self):
        """Initializes an empty verification result container."""
        self.entries = []
        return
        
    def __repr__(self):
        """Returns a textual representation of all collected entries."""
        return "entries:{}".format(self.entries)
        
    def success(self):
        """Indicates whether verification completed without findings."""
        return len(self.entries) == 0
        
    def failed(self):
        """Indicates whether any verification issues were recorded."""
        return len(self.entries) > 0
        
    def has_problem(self, problem_id):
        """Checks whether a specific problem has already been recorded."""
        for entry in self.entries:
            if entry.problem_id == problem_id:
                return True
        return False

    def add_problem_id(self, problem_id, data):
        """Adds a problem entry if it has not been recorded already."""
        if(not self.has_problem(problem_id)):
            self.entries.append(self.Entry(problem_id, data))
        
    def check_auto_gain_result(self, auto_gain_result, hints = None):
        """Checks the result of the auto-gain procedure for errors."""
        ret = True
        if not (auto_gain_result.found == True):
            self.add_problem_id(self.ProblemId.AUTO_GAIN_RESULT, auto_gain_result)
            ret = False

        return ret

    @staticmethod
    def expected_value(led_power):
        """Computes the expected RFU value for a given LED power using configured thresholds."""
        slope = (Verification._max_rfu - Verification._min_rfu) / (Verification._max_led - Verification._min_led)
        return Verification._min_rfu + slope * (led_power - Verification._min_led)

    @staticmethod
    def has_cuvette(sm: SingleMeasurement) -> bool:
        """Heuristic test for cuvette presence based on LED power and RFU."""
        expected = Verification.expected_value(sm.channel_470.led_power)
        return sm.delta() > expected * Verification._threshold_multiplier

    def check_single_measurement(self, single_measurement, hints = None, std_high_target_signal_factor = _DEFAULT_STD_HIGH_TARGET_SIGNAL_FACTOR):      
        """Checks a single measurement for saturation, cuvette presence, and expected levels."""
        ret = True

        if std_high_target_signal_factor is None:
            std_high_target_signal_factor = Verification._DEFAULT_STD_HIGH_TARGET_SIGNAL_FACTOR
        
        if single_measurement.channel_470.value >= self._max_signal:
            self.add_problem_id(self.ProblemId.SATURATION, single_measurement)
            ret = False            

        if hints != None and self.Hints.MUST_HAVE_CUVETTE in hints:
            if not (Verification.has_cuvette(single_measurement) == True):
                self.add_problem_id(self.ProblemId.CUVETTE_MISSING, single_measurement)
                ret = False
                
        if hints != None and self.Hints.STD_HIGH in hints:
            std_high_target = Verification._max_signal * std_high_target_signal_factor
            if not (single_measurement.channel_470.value >= (std_high_target - Verification._std_high_delta) and single_measurement.channel_470.value <= (std_high_target + Verification._std_high_delta)):
                self.add_problem_id(self.ProblemId.WRONG_LEVEL, single_measurement)
                ret = False

        return ret
        
    def check_measurement(self, measurement, hints = None):
        """Verifies a full air/sample measurement pair."""
        ret1 = self.check_single_measurement(measurement.air, self.Hints.MUST_HAVE_CUVETTE )
        ret2 = self.check_single_measurement(measurement.sample, (hints or self.Hints.NONE) | self.Hints.MUST_HAVE_CUVETTE)
        return ret1 and ret2

    def check_result(self, results, hints = None):
        """Validates computed results against negative concentration thresholds."""
        if results.concentration < Verification._threshold_negative_concentration:
            self.add_problem_id(self.ProblemId.NEGATIVE_CONCENTRATION, results)
            ret = False
        else:
            ret = True
        return ret

    def check_first_air_measurement_result(self, fam, hints):
        """Verifies the bounds of a first air measurement result."""
        ret1 = self.check_single_measurement(fam.min_measurement, self.Hints.MUST_HAVE_CUVETTE)
        ret2 = self.check_single_measurement(fam.max_measurement, self.Hints.MUST_HAVE_CUVETTE)
        return ret1 and ret2
        
    def check_first_sample_measurement_result(self, fsm, hints, std_high_target_signal_factor):
        """Verifies a first sample measurement result including auto-gain and standard high checks."""
        ret1 = self.check_auto_gain_result(fsm.auto_gain_result, hints)
        ret2 = self.check_single_measurement(fsm.measurement,  self.Hints.MUST_HAVE_CUVETTE | self.Hints.STD_HIGH, std_high_target_signal_factor = std_high_target_signal_factor)
        return ret1 and ret2
        
    def check(self, sample, hints = None, std_high_target_signal_factor = _DEFAULT_STD_HIGH_TARGET_SIGNAL_FACTOR):
        """Dispatches verification based on the type of sample provided."""
        if isinstance(sample, SingleMeasurement):
            return self.check_single_measurement(sample, hints, std_high_target_signal_factor = std_high_target_signal_factor)
        elif isinstance(sample, AutoGainResult):
            return self.check_auto_gain_result(sample, hints)
        elif isinstance(sample, FirstAirMeasurementResult):    
            return self.check_first_air_measurement_result(sample, hints)
        elif isinstance(sample, FirstSampleMeasurementResult):    
            return self.check_first_sample_measurement_result(sample, hints, std_high_target_signal_factor)
        elif isinstance(sample, Measurement):    
            return self.check_measurement(sample, hints)
        elif isinstance(sample, Results):
            return self.check_result(sample, hints)
        else:
            raise Exception("Unsupported class {}".format(type(sample)))
        
    def to_json(self):
        """Serializes all verification entries to a JSON-compatible list."""
        ret = []
        for entry in self.entries:
            ret.append(entry.to_json())
        return ret
        
    @staticmethod
    def from_json(node):
        """Restores verification entries from JSON."""
        ret = Verification()
        for entry in node:
            ret.entries.append(Verification.Entry.from_json(entry))
        return ret
