# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import json
import os
import threading
from contextlib import contextmanager

import serial.tools.list_ports

from .constants import USB
from .device import Device
from .kits import Default as DefaultKit
from .run import Run

_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def _resolve_path(working_dir, filename):
    if filename is None or os.path.isabs(filename):
        return filename
    return os.path.join(working_dir, filename)


def resolve_state_path(working_dir, device=None):
    return _resolve_path(working_dir, Run._resolve_state_filename(device=device))


def resolve_run_paths(working_dir, filename=None, device=None):
    working_dir = os.path.abspath(working_dir)
    os.makedirs(working_dir, exist_ok=True)
    data_file = _resolve_path(working_dir, filename)
    state_file = resolve_state_path(working_dir, device)
    return working_dir, data_file, state_file


def _run_state_name(value):
    if isinstance(value, Run.State):
        return value.name.lower()
    return str(value).lower()


def _read_json_if_exists(filename):
    if filename is None or not os.path.isfile(filename):
        return None
    with open(filename, "rb") as handle:
        return json.load(handle)


def _run_snapshot(run, state_file):
    data_file = getattr(run, "_filename", None)
    return {
        "state_file": state_file,
        "data_file": data_file,
        "device": "SIMULATION" if run.device.is_simulation else run.device.serial_number(),
        "nr_of_std_low": run.nr_of_std_low,
        "nr_of_std_high": run.nr_of_std_high,
        "concentration": run.concentration,
        "kit": run.kit.to_json(),
        "settling_time": run.settling_time,
        "no_air": getattr(run._algorithm, "name", None) == "V2",
        "count": run._count,
        "next_state": _run_state_name(run._state),
        "measurement_count": len(run.storage),
        "has_factors": run._factors is not None,
        "verification": run.verification.to_json(),
    }


def _lock_key(kind, value):
    normalized = os.path.abspath(value) if kind == "run" else value
    return "{}:{}".format(kind, normalized)


def _get_lock(kind, value):
    key = _lock_key(kind, value)
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


@contextmanager
def _acquire_lock(kind, value):
    lock = _get_lock(kind, value)
    with lock:
        yield


def _device_lock_value(device=None):
    return device or "__default__"


def _device_lock_is_busy(device=None):
    lock = _get_lock("device", _device_lock_value(device))
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
        return False
    return True


def _probe_device_info(device=None):
    evifluor = Device(device)
    try:
        return {
            "serialnumber": evifluor.serial_number(),
            "firmwareVersion": evifluor.firmware_version(),
            "productionnumber": evifluor.production_number(),
        }
    finally:
        evifluor.close()


def _device_from_state_file(state_file):
    state = _read_json_if_exists(state_file)
    if state is None:
        return None
    return state.get("device")


def get_device_info(device=None):
    with _acquire_lock("device", _device_lock_value(device)):
        return _probe_device_info(device)


def list_devices():
    devices = []
    for port in serial.tools.list_ports.comports():
        if port.vid == USB.VID and port.pid == USB.PID:
            devices.append({
                "device_id": port.serial_number,
                "port": port.device,
            })
    return devices


def run_selftest(device=None):
    with _acquire_lock("device", _device_lock_value(device)):
        evifluor = Device(device)
        try:
            payload = evifluor.selftest().to_json()
            payload["hasProblems"] = payload["result"] != 0
            return payload
        finally:
            evifluor.close()


def check_empty(device=None):
    with _acquire_lock("device", _device_lock_value(device)):
        evifluor = Device(device)
        try:
            return {
                "empty": evifluor.is_cuvette_holder_empty(),
            }
        finally:
            evifluor.close()


def init_run(nr_of_std_low, nr_of_std_high, concentration, working_dir=".", filename=None, device=None, no_air=False, kit=None, settling_time=None):
    if kit is None:
        kit = DefaultKit()
    working_dir, data_file, state_file = resolve_run_paths(working_dir, filename, device)
    with _acquire_lock("run", state_file):
        with _acquire_lock("device", _device_lock_value(device)):
            run = Run(
                nr_of_std_low,
                nr_of_std_high,
                concentration,
                path=working_dir if data_file is None else None,
                filename=data_file,
                device=device,
                no_air=no_air,
                kit=kit,
                settling_time=settling_time,
            )
            try:
                run.save_state(state_file)
                snapshot = _run_snapshot(run, state_file)
                snapshot["state"] = _read_json_if_exists(state_file)
                return snapshot
            finally:
                run.close()


def load_run_state(state_file):
    with _acquire_lock("run", state_file):
        run = Run.load_state(state_file)
        try:
            snapshot = _run_snapshot(run, state_file)
            snapshot["state"] = _read_json_if_exists(state_file)
            snapshot["data"] = _read_json_if_exists(snapshot["data_file"])
            return snapshot
        finally:
            run.close()


def measure_run(working_dir=".", filename=None, device=None, comment=None):
    _, _, state_file = resolve_run_paths(working_dir, filename, device)
    return measure_run_state(state_file, comment=comment)


def measure_run_state(state_file, comment=None):
    with _acquire_lock("run", state_file):
        device = _device_from_state_file(state_file)
        with _acquire_lock("device", _device_lock_value(device)):
            run = Run.load_state(state_file)
            try:
                run.measure(comment)
                run.save_state(state_file)
                snapshot = _run_snapshot(run, state_file)
                snapshot["state"] = _read_json_if_exists(state_file)
                snapshot["data"] = _read_json_if_exists(snapshot["data_file"])
                return snapshot
            finally:
                run.close()


def get_device_status(device=None):
    devices = list_devices()
    if device is None:
        if _device_lock_is_busy():
            return {
                "device_id": None,
                "status": "busy",
                "error": None,
            }
        for entry in devices:
            if _device_lock_is_busy(entry["device_id"]):
                return {
                    "device_id": entry["device_id"],
                    "status": "busy",
                    "error": None,
                }
        if len(devices) > 0:
            return {
                "device_id": devices[0]["device_id"],
                "status": "idle",
                "error": None,
            }
        return {
            "device_id": None,
            "status": "error",
            "error": "No available device found",
        }

    if device == "SIMULATION":
        return {
            "device_id": device,
            "status": "busy" if _device_lock_is_busy(device) else "idle",
            "error": None,
        }

    if _device_lock_is_busy(device):
        return {
            "device_id": device,
            "status": "busy",
            "error": None,
        }

    for entry in devices:
        if entry["device_id"] == device:
            return {
                "device_id": device,
                "status": "idle",
                "error": None,
            }

    return {
        "device_id": device,
        "status": "error",
        "error": f"Device '{device}' not found in available devices",
    }


def export_run(working_dir=".", filename=None, device=None):
    _, _, state_file = resolve_run_paths(working_dir, filename, device)
    return export_run_state(state_file)


def export_run_state(state_file):
    with _acquire_lock("run", state_file):
        run = Run.load_state(state_file)
        try:
            run.export_as_csv()
            snapshot = _run_snapshot(run, state_file)
            data_file = snapshot["data_file"]
            snapshot["csv_file"] = None if data_file is None else os.path.splitext(data_file)[0] + ".csv"
            return snapshot
        finally:
            run.close()
