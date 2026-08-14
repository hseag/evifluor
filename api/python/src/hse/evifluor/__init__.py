# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from . import constants, service
from .channel import Channel
from .constants import Color, DictKeys, Error, Index, Selftest, TypeOf
from .device import (
    AutoGainResult,
    Device,
    FirstAirMeasurementResult,
    FirstSampleMeasurementResult,
    SelfttestResult,
)
from .kits import Default, QubitTM_1X_dsDNA_High_Sensitivity_HS, QubitTM_1X_dsDNA_Broad_Range_BR
from .lookup_table import LookupTable
from .measurement import Algorithm, Factors, Measurement, Point, Results
from .normalized_rfu_csv_exporter import NormalizedRfuCsvExporter
from .run import Run
from .singlemeasurement import SingleMeasurement
from .storage import StorageMeasurement, StorageMeasurementEntry
from .verification import Verification
from .lookup_table import LookupTable
try:
    from ._version import __version__ as VERSION
except ImportError:
    VERSION = "0.0.0"

_constant_exports = {name: getattr(DictKeys, name) for name in dir(DictKeys) if name.isupper()}
globals().update(_constant_exports)

__all__ = [
    "VERSION",
    "Channel",
    "SingleMeasurement",
    "Results",
    "Point",
    "Factors",
    "Measurement",
    "Algorithm",
    "Default",
    "QubitTM_1X_dsDNA_High_Sensitivity_HS",
    "QubitTM_1X_dsDNA_Broad_Range_BR",
    "LookupTable",
    "AutoGainResult",
    "FirstAirMeasurementResult",
    "FirstSampleMeasurementResult",
    "SelfttestResult",
    "Device",
    "StorageMeasurementEntry",
    "StorageMeasurement",
    "NormalizedRfuCsvExporter",
    "Run",
    "Verification",
    "Color",
    "Error",
    "Index",
    "Selftest",
    "TypeOf",
    "DictKeys",
    "constants",
    "service",
    *_constant_exports,
]
