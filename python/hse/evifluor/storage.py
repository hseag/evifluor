# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

import csv
from datetime import datetime
import json
import os

from hse.evifluor import version
from hse.evifluor.constants import DictKeys
from hse.evifluor.measurement import Measurement, Results
from hse.evifluor.verification import Verification
from . import kits


class StorageMeasurementEntry:
    """Represents a stored measurement with optional comment, results, and raw JSON node."""

    def __init__(self, measurement, comment = None, results = None, node = None):
        """Initializes a storage entry with measurement data and optional metadata."""
        self.measurement = measurement
        self.comment     = comment
        self.results     = results
        self.node        = node
        
    def __repr__(self):
        """Returns a textual representation of the storage entry."""
        return "measurement:{} comment:{} results:{}".format(self.measurement, self.comment, self.results)
        
    def has_results(self):
        """Indicates whether calculated results are present."""
        if self.results is None:
            return False
        else:
            return True
            
    def apply_results(self, factors, kit = kits.Default()):
        """Applies calibration factors to compute results and updates the JSON node."""
        results = self.measurement.results(factors, kit)
        self.node[DictKeys.RESULTS] = results.to_json()
        if DictKeys.ERRORS in self.node:
            v = Verification.from_json(self.node[DictKeys.ERRORS])
        else:
            v = Verification()
        v.check(results)
        if v.failed():
            self.node[DictKeys.ERRORS] = v.to_json()
        
    @staticmethod
    def from_json(node):
        """Creates a StorageMeasurementEntry from a JSON node."""
        if DictKeys.RESULTS in node:
            results = Results.from_json(node[DictKeys.RESULTS])
        else:
            results = None

        if DictKeys.COMMENT in node:
            comment = node[DictKeys.COMMENT]
        else:
            comment = None
            
        return StorageMeasurementEntry(Measurement.from_json(node), comment, results, node)
        

class StorageMeasurement:
    """Handles storage and retrieval of measurements using JSON serialization."""

    def __init__(self, filename = None):
        """Initializes storage from an optional filename or creates an empty structure."""
        
        if filename is None:
            self.data = {DictKeys.MEASUREMENTS: []}
        else:
            with open(filename, 'rb') as f:
                self.data = json.load(f)
    
    def append(self, measurement, comment = None, logging = None, verification = None):
        """Appends a measurement and optional metadata to storage."""
        if isinstance(measurement, Measurement):
            m = measurement.to_json()
        else:
            raise Exception("Class not supported!")
        
        if comment:
            m[DictKeys.COMMENT] = comment

        if logging:
            m[DictKeys.LOGGING] = logging
            
        m[DictKeys.DATE_TIME] = datetime.now().isoformat()
            
        if verification != None and verification.failed():
            m[DictKeys.ERRORS] = verification.to_json()
            
        self.data[DictKeys.MEASUREMENTS].append(m)

    def append_with_results(self, measurement, results, comment = None, logging = None, verification = None):
        """Appends a measurement along with computed results and metadata."""
        if isinstance(measurement, Measurement):
            m = measurement.to_json()
        else:
            raise Exception("Class not supported!")
        
        if results:
            m[DictKeys.RESULTS] = results.to_json()
            
        if comment:
            m[DictKeys.COMMENT] = comment
            
        if logging:
            m[DictKeys.LOGGING] = logging
            
        m[DictKeys.DATE_TIME] = datetime.now().isoformat()

        if verification != None and verification.failed():
            m[DictKeys.ERRORS] = verification.to_json()
            
        self.data[DictKeys.MEASUREMENTS].append(m)

        
    def add_device_info(self, device, comment = None):
        """Adds device information and metadata to the storage document."""
        self.data[DictKeys.INFO] = { "date"              : datetime.now().isoformat(),
                                     "product"           : "eviFluor",
                                     "production_number" : device.production_number(),
                                     "serial_number"     : device.serial_number(),
                                     "firmware_version"  : device.firmware_version(),
                                     "comment"           : comment or "",
                                     "api"               : version.VERSION
                               }
                               
    def add_dict(self, key, value):
        """Inserts an arbitrary key/value pair into the storage document."""
        self.data[key] = value

    def save(self, filename):
        """Saves the storage data to disk in JSON format."""
        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=2)
            
    def measurements(self):
        """Returns the measurements reconstructed from storage."""
        ret = []
        for m in self.data[DictKeys.MEASUREMENTS]:
            ret.append(Measurement.from_json(m))
        return ret

    def results(self):
        """Returns the stored results."""
        ret = []
        for m in self.data[DictKeys.MEASUREMENTS]:
            ret.append(Results.from_json(m[DictKeys.RESULTS]))
        return ret
   
    def __getitem__(self, item):
        """Retrieves the entry at the specified index."""
        if item >= self.__len__():
            raise IndexError("CustomRange index out of range")
        return StorageMeasurementEntry.from_json(self.data[DictKeys.MEASUREMENTS][item])

    def __len__(self):
        """Returns the number of stored measurements."""
        return len(self.data[DictKeys.MEASUREMENTS])
    
    @staticmethod
    def export_as_csv(filenameJson, flat = False):
        """Exports stored measurements to CSV, optionally flattening channel values."""
        data = {}
        if os.path.isfile(filenameJson):
            with open(filenameJson, 'rb') as f:
                data = json.load(f)
        else:
            raise Exception("File {} not found".format(filenameJson))

        filenameCsv, _ = os.path.splitext(filenameJson)
        with open('{}.csv'.format(filenameCsv), 'w', newline='') as csvfile:
            if flat == True:
                fieldnames = [
                    DictKeys.COMMENT,
                    DictKeys.AIR_DARK,
                    DictKeys.AIR_VALUE,
                    DictKeys.AIR_LED_POWER,
                ]
                writer = csv.writer(csvfile, delimiter=";")
                for measurement in data[DictKeys.MEASUREMENTS]:
                    row = []
                    row.append(measurement.get(DictKeys.COMMENT, ""))
                    for value in measurement[DictKeys.VALUES]:
                        row.append(value[DictKeys.DARK])
                        row.append(value[DictKeys.VALUE])
                        row.append(value[DictKeys.LED_POWER])
                    print(row)
                    writer.writerow(row)
            else:
                fieldnames = [
                    DictKeys.COMMENT,
                    DictKeys.AIR_DARK,
                    DictKeys.AIR_VALUE,
                    DictKeys.AIR_LED_POWER,
                    DictKeys.SAMPLE_DARK,
                    DictKeys.SAMPLE_VALUE,
                    DictKeys.SAMPLE_LED_POWER,
                    DictKeys.CONCENTRATION,
                    DictKeys.RFU,
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for measurement in data[DictKeys.MEASUREMENTS]:
                    if measurement.get(DictKeys.SAMPLE) != None:
                        if DictKeys.RESULTS in measurement:
                            concentration = measurement[DictKeys.RESULTS][DictKeys.CONCENTRATION]
                            rfu = measurement[DictKeys.RESULTS].get(DictKeys.RFU, "")
                        else:
                            concentration = ""
                            rfu = ""

                        if DictKeys.AIR in measurement:
                            air_dark      = measurement[DictKeys.AIR][DictKeys.DARK]
                            air_value     = measurement[DictKeys.AIR][DictKeys.VALUE]
                            air_led_power = measurement[DictKeys.AIR][DictKeys.LED_POWER]
                        else:
                            air_dark      = ""
                            air_value     = ""
                            air_led_power = ""

                        if DictKeys.COMMENT in measurement:
                            comment       = measurement[DictKeys.COMMENT]
                        else:
                            comment       = ""

                        if DictKeys.SAMPLE in measurement:
                            sample_dark      = measurement[DictKeys.SAMPLE][DictKeys.DARK]
                            sample_value     = measurement[DictKeys.SAMPLE][DictKeys.VALUE]
                            sample_led_power = measurement[DictKeys.SAMPLE][DictKeys.LED_POWER]
                        else:
                            sample_dark      = ""
                            sample_value     = ""
                            sample_led_power = ""

                        if DictKeys.COMMENT in measurement:
                            comment       = measurement[DictKeys.COMMENT]
                        else:
                            comment       = ""

                        writer.writerow({
                            DictKeys.COMMENT:         comment,
                            DictKeys.AIR_DARK:        air_dark,
                            DictKeys.AIR_VALUE:       air_value,
                            DictKeys.AIR_LED_POWER:   air_led_power,
                            DictKeys.SAMPLE_DARK:     sample_dark,
                            DictKeys.SAMPLE_VALUE:    sample_value,
                            DictKeys.SAMPLE_LED_POWER: sample_led_power,
                            DictKeys.CONCENTRATION:   concentration,
                            DictKeys.RFU:             rfu,
                        })

    @staticmethod
    def exportAsCsv(filenameJson, flat = False):
        """Backwards-compatible alias for export_as_csv."""
        return __class__.export_as_csv(filenameJson, flat)
