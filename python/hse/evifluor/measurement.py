# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from enum import IntEnum
import math

from . import kits
from .constants import DictKeys
from .device import FirstAirMeasurementResult, FirstSampleMeasurementResult
from .singlemeasurement import SingleMeasurement


class Algorithm(IntEnum):
    """Measurement algorithms for converting signals to concentrations."""

    V1 = 0 # with air measurement
    V2 = 1 # without air measurement
    

class Results:
    """Represents the concentration result of a measurement, including RFU."""

    def __init__(self, concentration, rfu=None):
        """Initializes the result with the specified concentration and optional RFU."""
        self.concentration = concentration
        self.rfu = rfu
        
    def __repr__(self):
        """Returns a string representation of the concentration result."""
        return "concentration:{} rfu:{}".format(self.concentration, self.rfu)
        
    def to_json(self):
        """Converts the result to a JSON representation."""
        m = {
            DictKeys.CONCENTRATION: self.concentration
        }
        if self.rfu is not None:
            m[DictKeys.RFU] = self.rfu
        return m
        
    def __eq__(self, rhs):
        """Compares two results with a tolerance to account for floating-point rounding."""
        delta = 0.0000000000001
        if not math.isclose(self.concentration, rhs.concentration, rel_tol=delta):
            return False
        if self.rfu is None or rhs.rfu is None:
            return True
        return math.isclose(self.rfu, rhs.rfu, rel_tol=delta)

    @staticmethod
    def from_json(node):
        """Creates a Results instance from a JSON node."""
        return Results(node[DictKeys.CONCENTRATION], node.get(DictKeys.RFU))


class Point:
    """Represents a calibration point with concentration and signal value."""

    def __init__(self, concentration, value):
        """Initializes a Point with the given concentration and measured value."""
        self.concentration = concentration
        self.value         = value
        
    def __repr__(self):
        """Returns a string representation of the calibration point."""
        return "concentration:{} value:{}".format(self.concentration, self.value)

    def to_json(self):
        """Converts the point to a JSON representation."""
        return {
            "concentration": self.concentration,
            "value": self.value,
        }

    @staticmethod
    def from_json(node):
        """Creates a Point instance from JSON data."""
        return Point(node["concentration"], node["value"])
        

class Factors:
    """Holds calibration factors derived from standard measurements."""

    def __init__(self, std_low, std_high, measurement_std_low = 0.0, algorithm = None):
        """Initializes the factors with standard low/high points and metadata."""
        self.std_low               = std_low
        self.std_high              = std_high
        self.measurement_std_low   = measurement_std_low
        self.algorithm             = algorithm

    def __repr__(self):
        """Returns a textual representation of the calibration factors."""
        return "std_low:{} std_high:{} measurement_std_low:{} algorithm:{}".format(self.std_low, self.std_high, self.measurement_std_low, self.algorithm)

    def to_json(self):
        """Converts the factors to a JSON representation."""
        return {
            "std_low": self.std_low.to_json(),
            "std_high": self.std_high.to_json(),
            "measurement_std_low": self.measurement_std_low,
            "algorithm": int(self.algorithm) if self.algorithm is not None else None,
        }

    @staticmethod
    def from_json(node):
        """Creates a Factors instance from JSON data."""
        algorithm = node.get("algorithm")
        if algorithm is not None:
            algorithm = Algorithm(algorithm)
        return Factors(
            Point.from_json(node["std_low"]),
            Point.from_json(node["std_high"]),
            node.get("measurement_std_low", 0.0),
            algorithm,
        )


class Measurement:
    """Represents a measurement consisting of optional air and sample components."""

    def __init__(self, air, sample, comment = None):
        """Initializes the measurement from air and sample data or their aggregated results."""
        if isinstance(air, FirstAirMeasurementResult) and isinstance(sample, FirstSampleMeasurementResult):
            self.air             = air.adjust_to_led_power(sample.auto_gain_result.led_power)
            self.sample          = sample.measurement
        elif (air == None) and isinstance(sample, FirstSampleMeasurementResult):
            self.air             = None
            self.sample          = sample.measurement
        else:
            if air is None:
                self.air         = None
            else:
                self.air         = air
            self.sample          = sample
        self.comment  = comment
        
    # Returns a textual representation of the measurement.
    def __repr__(self):
        """Returns a textual representation of the measurement."""
        if self.air is None:
            return "sample:{} comment:{}".format(self.sample, self.comment)
        else:
            return "air:{} sample:{} comment:{}".format(self.air, self.sample, self.comment)

    @property
    def comment(self):
        """Gets the optional comment associated with the measurement."""
        return self._comment

    @comment.setter
    def comment(self, value):
        """Sets the optional comment associated with the measurement."""
        self._comment = value
             
    def value(self, algorithm = Algorithm.V1):
        """Computes the measurement value, optionally subtracting the air baseline."""
        if algorithm == Algorithm.V1:
            return self.sample.delta() - self.air.delta()
        else:
            return self.sample.delta()
        
    def concentration(self, factors, kit = kits.Default()):
        """Calculates the concentration using the provided calibration factors and kit."""
        return kit.fit(factors.std_low, factors.std_high, self.rfu(factors))

    def rfu(self, factors):
        """Calculates the RFU used as input for concentration calculation."""
        return self.value(factors.algorithm) - factors.measurement_std_low
        
    def results(self, factors, kit = kits.Default()):
        """Computes the measurement results using calibration factors and kit."""
        return Results(self.concentration(factors, kit), self.rfu(factors))
        
    def to_json(self):
        """Converts the measurement to a JSON representation."""
        if self.air is None:
            m = {DictKeys.SAMPLE: self.sample.to_json()}
        else:
            m = {
                DictKeys.AIR: self.air.to_json(),
                DictKeys.SAMPLE: self.sample.to_json(),
            }

        if self.comment != None:
            m[DictKeys.COMMENT] = self.comment

        return m
        
    @staticmethod
    def from_json(node):
        """Restores a Measurement from its JSON representation."""
        if DictKeys.AIR in node:
            return Measurement(
                SingleMeasurement.from_json(node[DictKeys.AIR]),
                SingleMeasurement.from_json(node[DictKeys.SAMPLE]),
                node.get(DictKeys.COMMENT),
            )
        else:
            return Measurement(
                None,
                SingleMeasurement.from_json(node[DictKeys.SAMPLE]),
                node.get(DictKeys.COMMENT),
            )

    @staticmethod     
    def calculate_factors(concentration_low, concentration_high, measurements_std_low, measurements_std_high, algorithm = Algorithm.V1):
        """Derives calibration factors from standard low and high measurements."""
        if isinstance(measurements_std_low, Measurement):
            measurements_std_low = [ measurements_std_low ]

        if isinstance(measurements_std_high, Measurement):
            measurements_std_high = [ measurements_std_high ]
        
        count_low  = len(measurements_std_low)
        count_high = len(measurements_std_high)
        std_low    = 0
        std_high   = 0
        
        if count_low >= 0:
            for measurement in measurements_std_low:
                std_low = std_low + measurement.value(algorithm)
            std_low = std_low / count_low
        else:
            std_low = 1

        if count_high >= 0:
            for measurement in measurements_std_high:
                std_high = std_high + (measurement.value(algorithm))
            std_high = std_high / count_high
        else:
            std_high = 1
            
        if algorithm == Algorithm.V2:
            return Factors(std_low = Point(concentration_low, std_low - std_low), std_high = Point(concentration_high, std_high - std_low), measurement_std_low = std_low, algorithm = algorithm)
        else:
            return Factors(std_low = Point(concentration_low, std_low), std_high = Point(concentration_high, std_high), algorithm = algorithm)
