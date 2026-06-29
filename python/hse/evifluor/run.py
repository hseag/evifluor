# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

import os
import json
import logging
from datetime import datetime
from enum import IntEnum
import time

from hse.evifluor.device import AutoGainResult, Device, FirstAirMeasurementResult, FirstSampleMeasurementResult
from hse.evifluor.measurement import Algorithm, Factors, Measurement
from hse.evifluor.singlemeasurement import SingleMeasurement
from hse.evifluor.storage import StorageMeasurement
from hse.evifluor.verification import Verification
from hse.evifluor.kits  import Default as DefaultKit
logger = logging.getLogger(__name__)

class Run:
    """Coordinates guided measurement runs including acquisition, verification, and storage."""

    class State(IntEnum):                            
        """Internal state machine for the guided run."""
        FIRST_AIR    = 0,
        FIRST_SAMPLE = 1
        AIR          = 2
        SAMPLE       = 3

    @staticmethod
    def _first_air_to_json(first_air):
        if first_air is None:
            return None
        return first_air.to_json()

    @staticmethod
    def _first_air_from_json(node):
        if node is None:
            return None
        return FirstAirMeasurementResult(
            SingleMeasurement.from_json(node["min_measurement"]),
            SingleMeasurement.from_json(node["max_measurement"]),
        )

    @staticmethod
    def _first_sample_to_json(first_sample):
        if first_sample is None:
            return None
        return {
            "autoGainResult": first_sample.auto_gain_result.to_json(),
            "measurement": first_sample.measurement.to_json(),
        }

    @staticmethod
    def _first_sample_from_json(node):
        if node is None:
            return None
        auto_gain = node["autoGainResult"]
        return FirstSampleMeasurementResult(
            AutoGainResult(auto_gain["found"], auto_gain["led_power"]),
            SingleMeasurement.from_json(node["measurement"]),
        )

    @staticmethod
    def _single_measurement_to_json(measurement):
        if measurement is None:
            return None
        return measurement.to_json()

    @staticmethod
    def _single_measurement_from_json(node):
        if node is None:
            return None
        return SingleMeasurement.from_json(node)

    @staticmethod
    def _safe_device_log_value(device):
        if device is None:
            return None
        if isinstance(device, str):
            return device
        return type(device).__name__
    
    def __init__(self, nr_of_std_low, nr_of_std_high, concentration, path = None, filename = None, device = None, no_air = False, kit = DefaultKit(), settling_time = None):
        """Initializes a new measurement run and opens the device if needed."""
        logger.debug(
            "Run.__init__ entry: nr_of_std_low=%s nr_of_std_high=%s concentration=%s path=%r filename=%r device=%r no_air=%s, kit=%s, settling_time=%s",
            nr_of_std_low,
            nr_of_std_high,
            concentration,
            path,
            filename,
            self._safe_device_log_value(device),
            no_air,
            kit,
            settling_time
        )
        self.nr_of_std_low  = nr_of_std_low
        self.nr_of_std_high = nr_of_std_high
        self.concentration  = concentration
        self._owns_device   = False
        self.kit            = kit
        if settling_time is not None:
            self.settling_time = settling_time
        else:
            self.settling_time  = self.kit.settling_time()

        if device is not None:
            if type(device) is str:
                self.device     = Device(device)
                self._owns_device = True
            else:
                self.device     = device
        else:
            self.device     = Device()
            self._owns_device = True
        self._count         = 0
        self.verification   = Verification()
        if no_air:
            self._algorithm     = Algorithm.V2
            self._state         = self.State.FIRST_SAMPLE
        else:
            self._state         = self.State.FIRST_AIR
            self._algorithm     = Algorithm.V1
        
        now = datetime.now()
        if filename is not None:
            self._filename  = filename
        else:
            self._filename  = "evifluor-{}-{}.json".format(self.device.serial_number(), now.strftime("%Y_%m_%d_%H_%M_%S"))
            
        if path is not None:
            self._filename = os.path.join(path, self._filename)
            
        self.storage        = StorageMeasurement()
        self._factors       = None
        logger.debug(
            "Run.__init__ exit: filename=%r device=%r state=%s count=%s has_factors=%s no_air=%s",
            self._filename,
            self._safe_device_log_value(self.device),
            self._state,
            self._count,
            self._factors is not None,
            self._algorithm == Algorithm.V2,
        )

    def __repr__(self):
        """Returns a textual summary of the run state."""
        return "device:{} nr_of_std_low:{} nr_of_std_high:{} concentration:{} state:{} count:{}".format(self.device, self.nr_of_std_low, self.nr_of_std_high, self.concentration, self._state, self._count)

    def close(self):
        """Releases the owned device handle, if any."""
        logger.debug(
            "Run.close entry: device=%r owns_device=%s",
            self._safe_device_log_value(self.device),
            self._owns_device,
        )
        if self._owns_device and self.device is not None:
            self.device.close()
        logger.debug("Run.close exit")

    @staticmethod
    def _resolve_state_filename(device = None, filename = None):
        if filename is not None:
            return filename
        if isinstance(device, str):
            return "evifluor-{}-state.json".format(device)
        if device is None:
            return "state.json"
        try:
            return "evifluor-{}-state.json".format(device.serial_number())
        except Exception:
            return "state.json"

    @staticmethod
    def load_state(filename = None):
        """Loads a run from a previously saved state file."""
        logger.debug("Run.load_state entry: filename=%r", filename)
        filename = Run._resolve_state_filename(filename = filename)
        with open(filename, "rb") as handle:
            state = json.load(handle)

        run = Run(
            state["nr_of_std_low"],
            state["nr_of_std_high"],
            state["concentration"],
            filename=state.get("filename"),
            device=state.get("device"),
            no_air=state.get("no_air", False),
            kit=DefaultKit.from_json(state["kit"]) if state.get("kit") is not None else DefaultKit(),
            settling_time=state.get("settling_time"),
        )
        run._count = state["count"]
        run._state = Run.State(state["state"])
        if state.get("factors") is not None:
            run._factors = Factors.from_json(state["factors"])
        run._first_air = Run._first_air_from_json(state.get("first_air"))
        run._first_sample = Run._first_sample_from_json(state.get("first_sample"))
        run._air = Run._single_measurement_from_json(state.get("air"))
        run._sample = Run._single_measurement_from_json(state.get("sample"))
        if run._filename is not None and os.path.isfile(run._filename):
            run.storage = StorageMeasurement(run._filename)
        else:
            run.storage = StorageMeasurement()

        logger.debug(
            "Run.load_state exit: resolved_filename=%r measurement_filename=%r state=%s count=%s has_factors=%s no_air=%s storage_len=%s",
            filename,
            run._filename,
            run._state,
            run._count,
            run._factors is not None,
            run._algorithm == Algorithm.V2,
            len(run.storage),
        )
        return run

    def save_state(self, filename = None):
        """Persists the current run state and measurement filename."""
        logger.debug(
            "Run.save_state entry: filename=%r state=%s count=%s measurement_filename=%r has_factors=%s no_air=%s",
            filename,
            self._state,
            self._count,
            self._filename,
            self._factors is not None,
            self._algorithm == Algorithm.V2,
        )
        filename = self._resolve_state_filename(self.device, filename)
        state = {
            "filename": self._filename,
            "nr_of_std_low": self.nr_of_std_low,
            "nr_of_std_high": self.nr_of_std_high,
            "concentration": self.concentration,
            "kit": self.kit.to_json(),
            "settling_time": self.settling_time,
            "no_air": self._algorithm == Algorithm.V2,
            "count": self._count,
            "state": int(self._state),
            "device": "SIMULATION" if self.device.is_simulation else self.device.serial_number(),
            "first_air": self._first_air_to_json(getattr(self, "_first_air", None)),
            "first_sample": self._first_sample_to_json(getattr(self, "_first_sample", None)),
            "air": self._single_measurement_to_json(getattr(self, "_air", None)),
            "sample": self._single_measurement_to_json(getattr(self, "_sample", None)),
            "factors": None if self._factors is None else self._factors.to_json(),
        }
        with open(filename, "w") as handle:
            json.dump(state, handle, indent=2)
        self.storage.save(self._filename)
        logger.debug(
            "Run.save_state exit: state_filename=%r measurement_filename=%r storage_len=%s",
            filename,
            self._filename,
            len(self.storage),
        )

    def re_calculate(self):
        """Recomputes calibration factors when enough standards exist and applies pending results."""
        logger.debug(
            "Run.re_calculate entry: nr_of_std_low=%s nr_of_std_high=%s concentration=%s storage_len=%s has_factors=%s no_air=%s",
            self.nr_of_std_low,
            self.nr_of_std_high,
            self.concentration,
            len(self.storage),
            self._factors is not None,
            self._algorithm == Algorithm.V2,
        )
        if self._factors is None and len(self.storage) == self.nr_of_std_low + self.nr_of_std_high:
            self._factors = Measurement.calculate_factors(0, self.concentration, self.storage.measurements()[self.nr_of_std_low:self.nr_of_std_high+self.nr_of_std_low:], self.storage.measurements()[0:self.nr_of_std_high:], algorithm = self._algorithm)
            
        if self._factors is not None:
            for entry in self.storage:
                if not entry.has_results():
                    entry.apply_results(self._factors, kit = self.kit)
        logger.debug(
            "Run.re_calculate exit: has_factors=%s storage_len=%s",
            self._factors is not None,
            len(self.storage),
        )

    def measure(self, comment = None):
        """Executes the next step in the measurement sequence and persists the result."""
        logger.debug(
            "Run.measure entry: comment=%r state=%s count=%s measurement_filename=%r no_air=%s",
            comment,
            self._state,
            self._count,
            self._filename,
            self._algorithm == Algorithm.V2,
        )
        if self._state == self.State.FIRST_AIR:
            self.verification = Verification()
            self._first_air = self.device.first_air_measurement()
            self.verification.check(self._first_air)
            self._state = self.State.FIRST_SAMPLE                        
        elif self._state == self.State.FIRST_SAMPLE:
            time.sleep(self.settling_time)
            
            if self.kit.std_high_target_signal_factor() is not None:
                self._first_sample = self.device.first_sample_measurement(self.kit.std_high_target_signal_factor())
            else:
                self._first_sample = self.device.first_sample_measurement()
            self.verification.check(self._first_sample, std_high_target_signal_factor = self.kit.std_high_target_signal_factor())
           
            if self._algorithm == Algorithm.V1:
                measurement = Measurement(self._first_air, self._first_sample)
                self._state = self.State.AIR
            else:
                measurement = Measurement(None, self._first_sample)
                self._state = self.State.SAMPLE

            self.storage.append(measurement, comment, logging = self.device.logging(), verification = self.verification)
        elif self._state == self.State.AIR:
            self.verification = Verification()
            self._air = self.device.measure()
            self.verification.check(self._air)
            self._state = self.State.SAMPLE
        elif self._state == self.State.SAMPLE:
            time.sleep(self.settling_time)
            
            self._sample = self.device.measure()
            self.verification.check(self._sample)
            
            if self._algorithm == Algorithm.V1:
                measurement = Measurement(self._air, self._sample)
                self._state = self.State.AIR
            else:
                measurement = Measurement(None, self._sample)
                self._state = self.State.SAMPLE
            
            self.storage.append(measurement, comment, logging = self.device.logging(), verification = self.verification)

        self.re_calculate()
        self.storage.save(self._filename)
        self._count = self._count + 1
        logger.debug(
            "Run.measure exit: next_state=%s count=%s storage_len=%s has_factors=%s",
            self._state,
            self._count,
            len(self.storage),
            self._factors is not None,
        )
    
    def check_empty(self) -> bool:
        """Returns True when the cuvette holder is empty according to the device."""
        logger.debug("Run.check_empty entry")
        ret = self.device.is_cuvette_holder_empty()
        logger.debug("Run.check_empty exit: result=%s", ret)
        return ret

    def export_as_csv(self):
        """Saves the stored measurements as CSV."""
        logger.debug("Run.export_as_csv entry: measurement_filename=%r", self._filename)
        self.storage.export_as_csv(self._filename)
        logger.debug("Run.export_as_csv exit: measurement_filename=%r", self._filename)
        
    def skip_air(self):
        """ Skips the air measurement, re-uses the last air value."""
        logger.debug("Run.skip_air entry: state=%s count=%s", self._state, self._count)
        if self._state == self.State.FIRST_AIR:
            raise Exception("State.FIRST_AIR: Can't skip the first air measurement!")
        elif self._state == self.State.FIRST_SAMPLE:
            raise Exception("State.FIRST_SAMPLE: Wrong state, expected state is AIR!")
        elif self._state == self.State.AIR:
            if not hasattr(self, "_air"):
                if hasattr(self, "_first_air") and hasattr(self, "_first_sample"):
                    self._air = self._first_air.adjust_to_led_power(self._first_sample.auto_gain_result.led_power)
                else:
                    raise Exception("State.AIR: air and first_air are None!")
            self._state = self.State.SAMPLE
        elif self._state == self.State.SAMPLE:
            raise Exception("State.SAMPLE: Wrong state, expected state is AIR!")
        else:
            raise Exception("State.?: Wrong state, expected state is AIR!")
        logger.debug("Run.skip_air exit: next_state=%s count=%s", self._state, self._count)
