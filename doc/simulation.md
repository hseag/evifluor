# eviFamily Simulation Guide

## 1. Overview

The repository contains simulators for eviDense UV Photometer and eviFluor Duo
Fluorometer. They support development, integration, demonstrations, and
automated testing without a physical device.

Both simulators expose the basic device protocol over TCP. Host-side interfaces
connect to the simulated device by opening it as `SIMULATION`. When started
without preloaded data, a simulator responds like its corresponding device but
does not replay a real measurement run.

Measurement data from a real or previously simulated run can be preloaded at
startup or with the `LOAD` control command. This is useful for repeatable
development, regression tests, and interface validation. A data file must match
the selected product.

## 2. Installation

The simulator is provided as a Python package with the console script
`hse-simulator`.

Example installation from the repository root:

```powershell
python -m pip install https://hseag.github.io/evifluor/pre-release/simulator/dist/hse_simulator-0.2.0-py3-none-any.whl
```

or download it

[`hse_simulator-0.2.0-py3-none-any.whl`](https://hseag.github.io/evifluor/pre-release/simulator/dist/hse_simulator-0.2.0-py3-none-any.whl){ download="hse_simulator-0.2.0-py3-none-any.whl" }


This installs:

- `hse-simulator`

## 3. Start a Simulator

Select the product to simulate:

| Product | Command | Default web UI port |
| --- | --- | --- |
| eviDense UV Photometer | `hse-simulator evidense` | `8011` |
| eviFluor Duo Fluorometer | `hse-simulator evifluor` | `8010` |

Both simulators listen on TCP port `5000`. Start only one simulator at a time
on the same host unless you provide a separate environment for the device
protocol port.

The matching web UI starts automatically unless `--no-web` is passed. The
default web UI bind host is `127.0.0.1`.

Useful common variants:

```powershell
hse-simulator --no-web evidense
hse-simulator --no-web evifluor
hse-simulator --verbose evidense
hse-simulator --verbose evifluor
hse-simulator evidense path/to/evidense-measurement-data.json
hse-simulator evifluor path/to/evifluor-measurement-data.json
hse-simulator --web-host 127.0.0.1 --web-port 8000 evidense
```

The eviFluor simulator also supports a workflow without air measurements:

```powershell
hse-simulator evifluor --no-air
```

`--no-air` applies only to eviFluor. When it is used with preloaded data, the
client workflow must use the same no-air mode so that the measurement sequence
matches the data.

## 4. Use the Simulator from an Interface

After the simulator is running, use `SIMULATION` as the device identifier in
the selected product interface.

For example, the Python low-level APIs open the simulated device as follows:

```python
# eviDense
from hse.evidense.device import Device

device = Device("SIMULATION")
```

```python
# eviFluor
from hse.evifluor.device import Device

device = Device("SIMULATION")
```

Use the interface package for the product currently being simulated; do not
connect both clients to the same simulator instance. The same `SIMULATION`
identifier is supported by the Python, C#, C CLI, and REST integration paths.

Examples for the Python command-line interfaces:

```powershell
python -m hse.evidense --device SIMULATION selftest
python -m hse.evifluor --device SIMULATION selftest
```

Use the product-specific interface documentation for the complete measurement
workflow and its product-specific parameters.

## 5. Simulator Control Commands

Send control commands to the running simulator with `hse-simulator sim ...`.
The following commands are available for both products:

```powershell
hse-simulator sim RESET
hse-simulator sim CHECKEMPTY 1
hse-simulator sim CHECKEMPTY 0
hse-simulator sim LOAD path/to/measurement-data.json
hse-simulator sim ZERO 1
hse-simulator sim SKIP 2
hse-simulator sim EXIT
```

| Command | Purpose |
| --- | --- |
| `RESET` | Reset the simulator state and clear loaded-data progress. |
| `CHECKEMPTY 0|1` | Set the reported cuvette-holder state. |
| `LOAD <file>` | Load product-matching measurement data for replay. |
| `ZERO 0|1` | Enable or disable zero-value measurement mode. |
| `SKIP <count>` | Skip preloaded measurement entries. |
| `EXIT` | Stop the running simulator. |

The eviFluor simulator additionally supports switching the no-air workflow:

```powershell
hse-simulator sim NO_AIR 1
hse-simulator sim NO_AIR 0
```

Use `NO_AIR` only with eviFluor. It is not an eviDense control command.

## 6. Typical Development Workflow

1. Start the simulator for the target product.
2. Optionally preload a matching measurement JSON file at startup or with
   `LOAD`.
3. Start the client application or script with the device identifier
   `SIMULATION`.
4. Use the web UI or `hse-simulator sim ...` commands to adjust simulator state
   as needed.
5. Run the normal measurement workflow against the simulator.
6. Validate positioning, cuvette handling, and the complete workflow on the
   physical device before productive use.
