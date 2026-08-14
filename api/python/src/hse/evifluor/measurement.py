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
        """Initializes a result instance.

        Args:
            concentration: Calculated concentration. The unit depends on the
                configured calibration standard.
            rfu: RFU value used as input for concentration calculation. Defaults
                to ``None``.
        """
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
        """Creates a results instance from JSON data.

        Args:
            node: JSON object containing ``concentration`` and optionally ``rfu``.

        Returns:
            A new :class:`Results` instance.
        """
        return Results(node[DictKeys.CONCENTRATION], node.get(DictKeys.RFU))


class Point:
    """Represents a calibration point with concentration and signal value."""

    def __init__(self, concentration, value):
        """Initializes a calibration point.

        Args:
            concentration: Concentration represented by the point.
            value: Measured signal value corresponding to ``concentration``.
        """
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
        """Creates a point instance from JSON data.

        Args:
            node: JSON object containing ``concentration`` and ``value``.

        Returns:
            A new :class:`Point` instance.
        """
        return Point(node["concentration"], node["value"])
        

class Factors:
    """Holds calibration factors derived from standard measurements."""

    def __init__(self, std_low, std_high, measurement_std_low = 0.0, algorithm = None):
        """Initializes factor data derived from standard measurements.

        Args:
            std_low: Calibration point for the low standard.
            std_high: Calibration point for the high standard.
            measurement_std_low: Averaged standard-low measurement used as
                sample-only baseline for algorithm ``V2``. Defaults to 0.0.
            algorithm: Algorithm used to derive the factors. Defaults to
                ``None``.
        """
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
        """Creates factors from JSON data.

        Args:
            node: JSON object containing serialized factor data.

        Returns:
            A new :class:`Factors` instance.
        """
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
        """Initializes a measurement from air/sample data or aggregate results.

        Args:
            air: Air reference measurement, or a
                :class:`FirstAirMeasurementResult`, or ``None`` when using the
                sample-only algorithm.
            sample: Sample measurement, or a
                :class:`FirstSampleMeasurementResult`.
            comment: Optional annotation stored with the measurement.
        """
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
        """Computes the measurement value.

        Args:
            algorithm: Measurement algorithm. ``Algorithm.V1`` subtracts the air
                baseline, while ``Algorithm.V2`` uses the sample value only.

        Returns:
            The background-corrected measurement signal.
        """
        if algorithm == Algorithm.V1:
            return self.sample.delta() - self.air.delta()
        else:
            return self.sample.delta()
        
    def concentration(self, factors, kit = kits.Default()):
        """Calculates concentration for this measurement.

        Args:
            factors: Calibration factors used for correction.
            kit: Kit used to convert the calibrated signal into concentration.
                Defaults to :class:`hse.evifluor.kits.Default`.

        Returns:
            The calculated concentration value.
        """
        return kit.fit(factors.std_low, factors.std_high, self.rfu(factors))

    def rfu(self, factors):
        """Calculates the RFU used for concentration fitting.

        Args:
            factors: Calibration factors containing the algorithm and optional
                sample-only baseline.

        Returns:
            The RFU value used as input for kit fitting.
        """
        return self.value(factors.algorithm) - factors.measurement_std_low
        
    def results(self, factors, kit = kits.Default()):
        """Computes measurement results using calibration factors and a kit.

        Args:
            factors: Factors used for calibration or adjustment.
            kit: Kit used for the final concentration fit. Defaults to
                :class:`hse.evifluor.kits.Default`.

        Returns:
            A :class:`Results` instance with concentration and RFU.
        """
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
        """Restores a measurement from JSON data.

        Args:
            node: JSON object containing serialized air/sample measurement data.

        Returns:
            A reconstructed :class:`Measurement` instance.
        """
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
        """Derives calibration factors from standard measurements.

        Args:
            concentration_low: Known concentration of the low standard.
            concentration_high: Known concentration of the high standard.
            measurements_std_low: One measurement or a list of measurements for
                the low standard.
            measurements_std_high: One measurement or a list of measurements for
                the high standard.
            algorithm: Algorithm used to evaluate the measurement values.

        Returns:
            A :class:`Factors` instance containing the derived calibration data.
        """
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
