# Python REST API

## 1. Scope

This chapter documents the Python-based REST API.
It complements the high-level API, the low-level API, and the Python command line interface.

## 2. Overview

The REST API provides HTTP access to the Python software stack of the eviFluor Duo Fluorometer.
It is intended for machine-to-machine integration and exposes a command model aligned with the Python CLI run workflow.

The server implementation is documented in [`hse.evifluor.rest_server`][rest-server-api], and the example client in [`hse.evifluor.rest_client`][rest-client-api].

The current REST API covers:

- device discovery
- device information
- self-test
- empty-check of the cuvette guide
- run initialization
- step-wise run measurement
- CSV export of a run
- retrieval of generated JSON run data
- download of generated JSON and CSV files

## 3. Installation and Startup

To install the published wheel directly from the documentation site, use:

```bash
python -m pip install https://hseag.github.io/evifluor/pre-release/python/dist/hse_evifluor-0.12.0b1-py3-none-any.whl
```

Start the REST API with:

```bash
evifluor-rest --host 127.0.0.1 --port 8000
```

or

```bash
python -m hse.evifluor.rest_server --host 127.0.0.1 --port 8000
```

To set a server-wide working directory for all generated run and CSV files, use:

```bash
python -m hse.evifluor.rest_server --host 127.0.0.1 --port 8000 --working-dir C:/data/evifluor-rest
```

To enable debug mode and write diagnostics to stderr instead of the rotating log file, use:

```bash
python -m hse.evifluor.rest_server --host 127.0.0.1 --port 8000 --debug
```

After startup, the interactive API documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## 4. Addressing Modes

The REST API supports two addressing modes.

### 4.1 Single-Device Mode

If exactly one device is available, the convenience endpoints without an explicit device ID can be used.

Examples:

- `GET /api/v1/device/info`
- `POST /api/v1/device/selftest`
- `GET /api/v1/device/checkempty`

### 4.2 Multi-Device Mode

If multiple devices are available, the explicit device routes should be used.

Examples:

- `GET /api/v1/devices/{device_id}/info`
- `POST /api/v1/devices/{device_id}/selftest`
- `GET /api/v1/devices/{device_id}/checkempty`

## 5. Main Endpoints

All requests and responses use JSON unless a file download endpoint is used.

The REST server manages run file locations on the server side. By default, generated files are stored in the `evifluor-rest-data` directory, or in the directory passed with `--working-dir`.

The REST server also configures backend logging:

- without `--debug`, backend logs are written to `evifluor-rest.log` in the selected working directory
- the log file uses rotation with backups
- with `--debug`, backend logs are written to stderr instead of the log file

### 5.1 `GET /api/v1/health`

Purpose:

- checks whether the REST service is running

Request:

- no request body

Response:

```json
{
  "status": "ok"
}
```

### 5.2 `GET /api/v1/version`

Purpose:

- returns the REST API version and backend software version

Request:

- no request body

Response:

```json
{
  "apiVersion": "v1",
  "backendVersion": "1.2.3"
}
```

### 5.3 `GET /api/v1/devices`

Purpose:

- returns the currently available devices

Request:

- no request body

Response:

```json
{
  "devices": [
    {
      "device_id": "P10006",
      "port": "COM14"
    }
  ]
}
```

Response fields:

- `devices`: list of discovered devices
- `device_id`: serial number used in explicit device routes
- `port`: host-side port or connection identifier

### 5.4 `GET /api/v1/device/info`

Purpose:

- returns device information in single-device mode

Request:

- no request body
- requires that exactly one device is available

Response:

```json
{
  "serialnumber": "P10006",
  "firmwareVersion": "1.2.3",
  "productionnumber": "2025-0001"
}
```

### 5.5 `GET /api/v1/devices/{device_id}/info`

Purpose:

- returns device information for the explicitly selected device

Path parameters:

- `device_id`: device serial number

Request:

- no request body

Response:

- same structure as `GET /api/v1/device/info`

### 5.6 `POST /api/v1/device/selftest`

Purpose:

- executes a self-test in single-device mode

Request:

- no request body
- requires that exactly one device is available

Response:

```json
{
  "result": 0,
  "hasProblems": false
}
```

Response fields:

- `result`: numeric self-test result code
- `hasProblems`: convenience flag derived from `result`
- additional fields contain the detailed self-test payload returned by the backend

### 5.7 `POST /api/v1/devices/{device_id}/selftest`

Purpose:

- executes a self-test for the explicitly selected device

Path parameters:

- `device_id`: device serial number

Request:

- no request body

Response:

- same structure as `POST /api/v1/device/selftest`

### 5.8 `GET /api/v1/device/checkempty`

Purpose:

- checks whether the cuvette guide is empty in single-device mode

Request:

- no request body
- requires that exactly one device is available

Response:

```json
{
  "empty": true
}
```

### 5.9 `GET /api/v1/devices/{device_id}/checkempty`

Purpose:

- checks whether the cuvette guide is empty for the explicitly selected device

Path parameters:

- `device_id`: device serial number

Request:

- no request body

Response:

```json
{
  "empty": true
}
```

### 5.10 `GET /api/v1/device/status`

Purpose:

- returns a simple service-side device status in single-device mode

Request:

- no request body

Response:

```json
{
  "device_id": "P10006",
  "status": "idle",
  "serialnumber": "P10006",
  "firmwareVersion": "1.2.3",
  "productionnumber": "2025-0001"
}
```

Response fields:

- `device_id`: resolved device identifier
- `status`: current service-side status
- `serialnumber`, `firmwareVersion`, `productionnumber`: same information as the `info` endpoint

### 5.11 `GET /api/v1/devices/{device_id}/status`

Purpose:

- returns a simple service-side device status for the explicitly selected device

Path parameters:

- `device_id`: device serial number

Request:

- no request body

Response:

- same structure as `GET /api/v1/device/status`

### 5.12 `POST /api/v1/runs`

Purpose:

- initializes a new run

Request:

```json
{
  "device_id": "P10006",
  "nr_of_std_low": 2,
  "nr_of_std_high": 2,
  "concentration": 10.0,
  "no_air": false
}
```

Request fields:

- `device_id`: optional in single-device mode, required for explicit multi-device selection
- `nr_of_std_low`: number of `standard low` measurements at the beginning of the run
- `nr_of_std_high`: number of `standard high` measurements at the beginning of the run
- `concentration`: concentration assigned to the `standard high`
- `no_air`: optional boolean flag that omits separate air measurements

Response:

```json
{
  "run_id": "ZXZpZmx1b3ItUDEwMDA2LXN0YXRlLmpzb24",
  "device": "P10006",
  "nr_of_std_low": 2,
  "nr_of_std_high": 2,
  "concentration": 10.0,
  "no_air": false,
  "count": 0,
  "next_state": "first_air",
  "measurement_count": 0,
  "has_factors": false,
  "state": {
    "nr_of_std_low": 2,
    "nr_of_std_high": 2,
    "concentration": 10.0,
    "count": 0,
    "state": 0,
    "no_air": false
  }
}
```

Response fields:

- `run_id`: opaque run identifier used in all run endpoints
- `device`: selected device
- `nr_of_std_low`: configured number of `standard low` measurements
- `nr_of_std_high`: configured number of `standard high` measurements
- `concentration`: configured concentration of the `standard high`
- `no_air`: whether the run omits separate air measurements
- `count`: number of completed `run measure` steps
- `next_state`: next expected state in the run state machine
- `measurement_count`: number of completed stored measurements
- `has_factors`: whether standard-derived factors are available
- `state`: current serialized run state without internal server-side file paths

Behavior:

- the measurement order must be `standard high`, `standard low`, then the samples
- `standard high` must come first because the initial automatic gain adjustment is based on this measurement sequence

### 5.13 `GET /api/v1/runs/{run_id}`

Purpose:

- returns the current run snapshot

Path parameters:

- `run_id`: run identifier returned by `POST /api/v1/runs`

Request:

- no request body

Response:

- same structure as the `POST /api/v1/runs` response
- may additionally contain `data` if a data file already exists

### 5.14 `POST /api/v1/runs/{run_id}/measure`

Purpose:

- executes the next run step

Path parameters:

- `run_id`: run identifier

Request:

```json
{
  "comment": "sample 1"
}
```

Request fields:

- `comment`: optional comment applied to the completed measurement entry at the sample step

Response:

- same general structure as `GET /api/v1/runs/{run_id}`

Behavior in normal mode:

- first call performs the first-air step
- second call performs the first-sample step and appends the first completed measurement
- subsequent calls alternate between air and sample measurements

Behavior with `no_air=true`:

- the first call performs the first-sample step and appends the first completed measurement
- subsequent calls perform sample-only measurements and append one measurement per call

### 5.15 `POST /api/v1/runs/{run_id}/export/csv`

Purpose:

- exports the current run data as CSV and returns the generated CSV file directly

Path parameters:

- `run_id`: run identifier

Request:

- no request body

Response:

- response body contains the generated CSV file content
- media type: `text/csv`

Behavior:

- the server writes or updates the CSV file on disk
- the same request returns the generated CSV content to the client

### 5.16 `GET /api/v1/runs/{run_id}/data`

Purpose:

- returns the generated JSON run data directly

Path parameters:

- `run_id`: run identifier

Request:

- no request body

Response:

- the full JSON measurement data file
- structure as documented in the user manual JSON data file format section

### 5.17 `GET /api/v1/runs/{run_id}/file/json`

Purpose:

- downloads the JSON run data file

Path parameters:

- `run_id`: run identifier

Request:

- no request body

Return:

- file download with media type `application/json`

### 5.18 `GET /api/v1/runs/{run_id}/file/csv`

Purpose:

- downloads the CSV export file

Path parameters:

- `run_id`: run identifier

Request:

- no request body

Return:

- file download with media type `text/csv`

## 6. Relationship to the Python CLI

The REST API is aligned with the Python CLI and mirrors the same main workflow concepts:

- `info`
- `selftest`
- `checkempty`
- `run init`
- `run measure`
- `run export`

The difference is only the transport:

- the CLI is shell-based
- the REST API is HTTP- and JSON-based

## 7. Example Workflow

The following example demonstrates the same workflow as the high-level Python example, but through the REST API:

```python
from hse.evifluor.rest_client import RestClient


def main():
    client = RestClient()

    run = client.run_init(
        nr_of_std_low=2,
        nr_of_std_high=2,
        concentration=10.0,
    )
    run_id = run["run_id"]

    sample_order = [
        "std high 1",
        "std high 2",
        "std low 1",
        "std low 2",
        "sample 1",
        "sample 2",
    ]

    for sample_name in sample_order:
        # The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
        if not client.checkempty()["empty"]:
            raise RuntimeError("Cuvette holder must be empty before the measurement")
        # Move the empty cuvette into the cuvette guide and start the air measurement.
        client.run_measure(run_id)
        # Dispense the liquid into the cuvette and start the sample measurement.
        client.run_measure(run_id, sample_name)
        # Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

    csv_text = client.run_export_csv(run_id)
    print(csv_text)


if __name__ == "__main__":
    main()
```

If the run should omit air measurements, enable `no_air` during `run_init()`:

```python
from hse.evifluor.rest_client import RestClient


def main():
    client = RestClient()

    run = client.run_init(
        nr_of_std_low=2,
        nr_of_std_high=2,
        concentration=10.0,
        no_air=True,
    )
    run_id = run["run_id"]

    sample_order = [
        "std high 1",
        "std high 2",
        "std low 1",
        "std low 2",
        "sample 1",
        "sample 2",
    ]

    for sample_name in sample_order:
        # The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
        if not client.checkempty()["empty"]:
            raise RuntimeError("Cuvette holder must be empty before the measurement")
        # Dispense the liquid into the cuvette and start the sample measurement.
        client.run_measure(run_id, sample_name)
        # Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

    csv_text = client.run_export_csv(run_id)
    print(csv_text)


if __name__ == "__main__":
    main()
```

This example uses the Python REST client in:

- [module/python/hse/evifluor/rest_client.py](/abs/c:/scm/hse/colibri/evifluor/module/python/hse/evifluor/rest_client.py:1)

## 8. Error Handling

The REST API returns structured JSON errors for invalid requests, device problems, and run-state problems.

Typical categories are:

- invalid request parameters
- missing device
- multiple devices when a single-device route is used
- invalid run identifier
- missing run data file
- backend execution errors from the device or run logic

## 9. Notes

- The REST API is implemented on top of the existing Python service layer.
- Device and run cleanup is handled even if a request fails.
- The REST API is intended for Windows-based integration scenarios.
- The `--working-dir` option controls both generated data files and the default log file location.
- The `--debug` option enables stderr logging for easier interactive troubleshooting.

[rest-server-api]: https://hseag.github.io/evifluor/pre-release/api/python/api/hse.evifluor.rest_server.html
[rest-client-api]: https://hseag.github.io/evifluor/pre-release/api/python/api/hse.evifluor.rest_client.html
