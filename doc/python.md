# Python Interfaces

## 1. Overview

This document is the entry point for the Python software interfaces of the eviFluor Duo Fluorometer.

For the generated Python API reference, see [Python API documentation][python-api-docs].

### 1.2 Available Python Interfaces

The Python package provides four different interfaces for working with the eviFluor Duo Fluorometer:

- a high-level API based on `Run`
- a low-level API based on direct `Device` access
- a command line interface for scripting and operational use
- a Python-based REST API for integration with external software

## 2. Version

This documentation describes Python package version `0.12.0-pre2`.

## 3. Installation

To install the published wheel directly from the documentation site, use:

```bash
python -m pip install https://hseag.github.io/evifluor/pre-release/python/dist/hse_evifluor-0.12.0rc2-py3-none-any.whl
```

Runtime dependency:

- `pyserial>=3.5`

Optional REST dependencies:

- `fastapi>=0.110`
- `uvicorn>=0.29`

After installation, the Python CLI is available as:

```bash
evifluor --help
```

The package can also be started directly as a module:

```bash
python -m hse.evifluor --help
```

The REST API can be installed as:

```bash
python -m pip install "hse-evifluor[rest] @ https://hseag.github.io/evifluor/pre-release/python/dist/hse_evifluor-0.12.0rc2-py3-none-any.whl"
```

Then start it as:

```bash
evifluor-rest --host 127.0.0.1 --port 8000
```

or

```bash
python -m hse.evifluor.rest_server --host 127.0.0.1 --port 8000
```

Recommended setup:

- use a virtual environment
- verify that the device is accessible on the host system

## 4. Which Interface to Use

### 4.1 Python High-Level API

Use the high-level API if you want a guided workflow with minimal application code.

Typical use cases:

- measurement workflows driven by a liquid handler
- automatic factor handling after standards are measured
- automatic persistence of run data
- resumed workflows based on saved state
- standard operational workflows with minimal glue code

Main characteristics:

- built around the `Run` class
- hides most of the step-by-step device interaction
- suitable for standard measurement workflows

See:

- [Python High-Level API](./python-high-level.md)

### 4.2 Python Low-Level API

Use the low-level API if you need full control over the measurement sequence.

Typical use cases:

- custom application logic
- explicit control of air and sample steps
- direct access to device information and raw measurements
- advanced integrations that should not depend on the `Run` state machine

Main characteristics:

- built around the `Device` class and related data classes
- explicit acquisition and calculation steps
- best suited for custom integrations

See:

- [Python Low-Level API](./python-low-level.md)

### 4.3 Python Command Line Interface

Use the CLI if you want to script or operate the device without writing a Python application.

Typical use cases:

- shell-based automation
- service and support workflows
- quick manual checks on connected devices
- exporting persisted measurement data

Main characteristics:

- available as `evifluor`
- suitable for operational and scripted workflows
- exposes common device and run commands directly on the shell

See:

- [Python Command Line Interface](./python-cli.md)

### 4.4 Python REST API

Use the REST API if you want to control the device from external software over HTTP.

Typical use cases:

- integration with applications that are not written in Python
- local service-style deployments
- network-facing orchestration on a host system

Main characteristics:

- available as `evifluor-rest`
- exposes device and run operations through HTTP endpoints
- suited for process boundaries where a Python library cannot be linked directly

See:

- [Python REST API](./python-rest.md)

## 5. Recommended Reading Order

For most users, the best order is:

1. Read this document first.
2. Continue with [Python High-Level API](./python-high-level.md) if you want the guided workflow.
3. Continue with [Python Low-Level API](./python-low-level.md) if you need direct control.
4. Continue with [Python Command Line Interface](./python-cli.md) or [Python REST API](./python-rest.md) if you need an operational interface instead of an in-process API.
5. Use [Kit Reference](./kit.md) for predefined kits, fit models, and kit-specific settings.

[python-api-docs]: https://hseag.github.io/evifluor/pre-release/doc/api/python/modules.html
