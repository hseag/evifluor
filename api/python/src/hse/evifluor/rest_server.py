# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import argparse
import base64
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import service
from .kits import Default as DefaultKit
try:
    from ._version import __version__ as VERSION
except ImportError:
    VERSION = "0.0.0"


def _resolve_log_file(args):
    """Resolves the REST server log file path.

    Args:
        args: Parsed CLI arguments. ``working_dir`` is used when available.

    Returns:
        Absolute path to the REST server log file.
    """
    if hasattr(args, "working_dir") and args.working_dir is not None:
        log_dir = os.path.abspath(args.working_dir)
    else:
        log_dir = os.getcwd()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "evifluor-rest.log")


def _configure_logging(args):
    """Configures logging for the REST server process.

    Args:
        args: Parsed CLI arguments controlling debug mode and working directory.
    """
    logger = logging.getLogger("hse.evifluor")

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(logging.DEBUG)

    if args.debug:
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = RotatingFileHandler(
            _resolve_log_file(args),
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def _encode_run_id(state_file: str) -> str:
    """Encodes a state-file path into an opaque run identifier.

    Args:
        state_file: Absolute path to the run-state file.

    Returns:
        URL-safe run identifier.
    """
    return base64.urlsafe_b64encode(state_file.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_run_id(run_id: str, storage_dir: str) -> str:
    """Decodes and validates a run identifier.

    Args:
        run_id: Encoded run identifier from the API.
        storage_dir: Allowed storage directory that decoded paths must stay
            inside.

    Returns:
        Validated absolute state-file path.
    """
    padding = "=" * (-len(run_id) % 4)
    try:
        state_file = base64.urlsafe_b64decode((run_id + padding).encode("ascii")).decode("utf-8")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid run_id") from exc

    state_file_path = Path(state_file).resolve()
    storage_dir_path = Path(storage_dir).resolve()
    try:
        state_file_path.relative_to(storage_dir_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run_id") from exc

    return str(state_file_path)


def _with_run_id(snapshot: dict) -> dict:
    """Attaches the encoded run identifier to a run snapshot.

    Args:
        snapshot: Service-layer snapshot containing ``state_file``.

    Returns:
        Copy of ``snapshot`` with ``run_id`` added and ``state_file`` removed.
    """
    payload = dict(snapshot)
    payload["run_id"] = _encode_run_id(snapshot["state_file"])
    payload.pop("state_file", None)
    return payload


def _resolve_existing_file(filename: Optional[str], detail: str) -> str:
    """Validates that a file exists for file-download endpoints.

    Args:
        filename: Candidate file path.
        detail: Error detail used when the file is missing.

    Returns:
        Existing file path.
    """
    if filename is None or not os.path.isfile(filename):
        raise HTTPException(status_code=404, detail=detail)
    return filename


def _storage_dir(working_dir: Optional[str] = None) -> str:
    """Resolves and creates the storage directory used by the REST server.

    Args:
        working_dir: Optional explicit storage directory.

    Returns:
        Absolute path to the storage directory.
    """
    base = working_dir if working_dir is not None else "evifluor-rest-data"
    path = os.path.abspath(base)
    os.makedirs(path, exist_ok=True)
    return path


def _available_devices() -> list[dict]:
    return service.list_devices()


def _resolve_single_device_id() -> Optional[str]:
    devices = _available_devices()
    if len(devices) == 0:
        raise HTTPException(status_code=404, detail="No device found")
    if len(devices) > 1:
        raise HTTPException(status_code=409, detail="Multiple devices available. Use the /devices/{device_id}/... routes.")
    return devices[0]["device_id"]


class RunInitRequest(BaseModel):
    """Request body for run initialization."""

    device_id: Optional[str] = None
    nr_of_std_low: int
    nr_of_std_high: int
    concentration: float
    kit: str = "Default"
    k1: Optional[float] = None
    k2: Optional[float] = None
    k3: Optional[float] = None
    lookup_table: Optional[list[dict]] = None
    settling_time: Optional[float] = None
    no_air: bool = False


class RunMeasureRequest(BaseModel):
    """Request body for run measurement steps."""

    comment: Optional[str] = None


def create_app(working_dir: Optional[str] = None) -> FastAPI:
    """Creates the FastAPI application.

    Args:
        working_dir: Optional storage directory used for run files and exports.

    Returns:
        Configured :class:`fastapi.FastAPI` application.
    """
    storage_dir = _storage_dir(working_dir)

    def decode_run_id(run_id: str) -> str:
        return _decode_run_id(run_id, storage_dir)

    app = FastAPI(
        title="eviFluor REST API",
        version=VERSION,
        description="REST API for the eviFluor Python CLI and run workflow.",
    )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/version")
    def version():
        return {"apiVersion": "v1", "backendVersion": VERSION}

    @app.get("/api/v1/devices")
    def list_devices():
        return {"devices": _available_devices()}

    @app.get("/api/v1/device/info")
    def device_info():
        return service.get_device_info(_resolve_single_device_id())

    @app.post("/api/v1/device/selftest")
    def device_selftest():
        return service.run_selftest(_resolve_single_device_id())

    @app.get("/api/v1/device/checkempty")
    def device_checkempty():
        return service.check_empty(_resolve_single_device_id())

    @app.get("/api/v1/device/status")
    def device_status():
        return service.get_device_status()

    @app.get("/api/v1/devices/{device_id}/info")
    def device_info_by_id(device_id: str):
        return service.get_device_info(device_id)

    @app.post("/api/v1/devices/{device_id}/selftest")
    def device_selftest_by_id(device_id: str):
        return service.run_selftest(device_id)

    @app.get("/api/v1/devices/{device_id}/checkempty")
    def device_checkempty_by_id(device_id: str):
        return service.check_empty(device_id)

    @app.get("/api/v1/devices/{device_id}/status")
    def device_status_by_id(device_id: str):
        return service.get_device_status(device_id)

    @app.post("/api/v1/runs")
    def run_init(request: RunInitRequest):
        device_id = request.device_id if request.device_id is not None else _resolve_single_device_id()
        factory_kwargs = {}
        if request.k1 is not None:
            factory_kwargs["k1"] = request.k1
        if request.k2 is not None:
            factory_kwargs["k2"] = request.k2
        if request.k3 is not None:
            factory_kwargs["k3"] = request.k3
        if request.lookup_table is not None:
            factory_kwargs["lookup_table"] = request.lookup_table

        snapshot = service.init_run(
            request.nr_of_std_low,
            request.nr_of_std_high,
            request.concentration,
            working_dir=storage_dir,
            filename=None,
            device=device_id,
            no_air=request.no_air,
            kit=DefaultKit.factory(request.kit, **factory_kwargs),
            settling_time=request.settling_time,
        )
        return _with_run_id(snapshot)

    @app.get("/api/v1/runs/{run_id}")
    def run_get(run_id: str):
        return _with_run_id(service.load_run_state(decode_run_id(run_id)))

    @app.post("/api/v1/runs/{run_id}/measure")
    def run_measure(run_id: str, request: RunMeasureRequest):
        return service.measure_run_values_state(decode_run_id(run_id), comment=request.comment)

    @app.get("/api/v1/runs/{run_id}/results")
    def run_results(run_id: str):
        return service.load_run_results_state(decode_run_id(run_id))

    @app.get("/api/v1/runs/{run_id}/verifications")
    def run_verifications(run_id: str):
        return service.load_run_verifications_state(decode_run_id(run_id))

    @app.post("/api/v1/runs/{run_id}/export/csv")
    def run_export(run_id: str):
        snapshot = service.export_run_state(decode_run_id(run_id))
        csv_file = _resolve_existing_file(snapshot.get("csv_file"), "Run CSV file not found")
        return FileResponse(csv_file, media_type="text/csv", filename=Path(csv_file).name)

    @app.get("/api/v1/runs/{run_id}/data")
    def run_data(run_id: str):
        snapshot = service.load_run_state(decode_run_id(run_id))
        if snapshot["data"] is None:
            raise HTTPException(status_code=404, detail="Run data file not found")
        return snapshot["data"]

    @app.get("/api/v1/runs/{run_id}/file/json")
    def run_json_file(run_id: str):
        snapshot = service.load_run_state(decode_run_id(run_id))
        data_file = _resolve_existing_file(snapshot.get("data_file"), "Run data file not found")
        return FileResponse(data_file, media_type="application/json", filename=Path(data_file).name)

    @app.get("/api/v1/runs/{run_id}/file/csv")
    def run_csv_file(run_id: str):
        snapshot = service.export_run_state(decode_run_id(run_id))
        csv_file = _resolve_existing_file(snapshot.get("csv_file"), "Run CSV file not found")
        return FileResponse(csv_file, media_type="text/csv", filename=Path(csv_file).name)

    return app


app = create_app()


def build_parser():
    """Builds the REST server command-line parser.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="python -m hse.evifluor.rest_server",
        description="Start the eviFluor REST API server.",
    )
    parser.add_argument("--debug", action="store_true", help="Print full traceback on errors")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--working-dir",
        default="evifluor-rest-data",
        help="Working directory for generated run and CSV files",
    )
    return parser


def main(argv=None):
    """REST server entry point.

    Args:
        argv: Optional argument list. When omitted, arguments are read from
            ``sys.argv``.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args)

    import uvicorn

    uvicorn.run(create_app(args.working_dir), host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
