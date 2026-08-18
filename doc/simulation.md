# Simulation Guide

## 1. Overview

The repository contains an eviFluor simulator for development and testing without a physical device.
The simulator exposes the same basic workflow over TCP that the software interfaces use when a device is opened as `"SIMULATION"`.
When started without preloaded data, the simulator behaves like an eviFluor that currently does not measure a cuvette with real sample data.
It still responds like a device and returns simulated values for the normal workflow.

With `LOAD`, an existing measurement JSON file from a real or previously simulated run can be loaded and replayed step by step.
This is useful for repeating known runs during development, regression tests, and interface validation.
If `NO_AIR` is enabled, `LOAD` interprets the loaded file in no-air mode as well.
In that case, the client workflow must also be started in no-air mode so that the measurement sequence matches the loaded data.

The simulator package is located in [`simulator`](../simulator).

## 2. Installation

The simulator is provided as a Python package with the console script `hse-simulator`.

Example installation from the repository root:

```powershell
python -m pip install https://hseag.github.io/evifluor/pre-release/simulator/dist/hse_simulator-0.1.0-py3-none-any.whl
```

This installs:

- `hse-simulator`

## 3. Start the eviFluor Simulator

Start the default eviFluor simulator with:

```powershell
hse-simulator evifluor
```

Behavior:

- the simulator listens on TCP port `5000`
- the matching web UI starts automatically unless `--no-web` is passed
- the default web UI bind host is `127.0.0.1`
- the default web UI port for `evifluor` is `8010`

Useful variants:

```powershell
hse-simulator evifluor --no-air
hse-simulator evifluor .\test\testdata\evifluor-P10006-2025_04_24_16_18_09.json
hse-simulator --no-web evifluor
hse-simulator --web-host 127.0.0.1 --web-port 8000 evifluor
hse-simulator --verbose evifluor
```

Meaning of the most important options:

- `--no-air`: starts the simulator in the sample-only workflow
- `<data file>`: preloads measurement values from a JSON file
- `--no-web`: disables the browser-based control UI
- `--web-host` and `--web-port`: configure where the web UI is exposed
- `--verbose`: prints request and response details

## 4. Interface Examples

After the simulator is running, all supported interfaces can be pointed to the simulated device.
The important selector is the device name `"SIMULATION"`.

### 4.1 C CLI

The C command line tool can run against the simulator by passing `--device SIMULATION`.

Example:

```powershell
evifluor-cli --device SIMULATION selftest
evifluor-cli --device SIMULATION empty
evifluor-cli --device SIMULATION run init 2 2 10
evifluor-cli --device SIMULATION run checkempty
evifluor-cli --device SIMULATION run measure
evifluor-cli --device SIMULATION run measure "std high 1"
```

See also [C Command Line Interface](./c-cli.md).

### 4.2 C# Low-Level API

In the low-level C# API, open the device as `"SIMULATION"`:

```csharp
using Hse.EviFluor;

using var device = new Device("SIMULATION");

var selftest = device.SelfTest();
bool empty = device.IsCuvetteHolderEmpty();
var firstAir = device.FirstAirMeasurement();
var firstSample = device.FirstSampleMeasurement();
```

See also [C# Low-Level API](./csharp-low-level.md).

### 4.3 C# High-Level API

In the high-level C# API, create the run with `device: "SIMULATION"`:

```csharp
using Hse.EviFluor;

var run = new Run(
    nrOfStdLow: 2,
    nrOfStdHigh: 2,
    concentration: 10.0,
    device: "SIMULATION");

if (!run.checkEmpty())
{
    throw new InvalidOperationException("Cuvette holder must be empty before the measurement");
}

run.measure();
run.measure("std high 1");
```

See also [C# High-Level API](./csharp-high-level.md).

### 4.4 Python Low-Level API

In the low-level Python API, open the device as `"SIMULATION"`:

```python
from hse.evifluor.device import Device

device = Device("SIMULATION")

selftest = device.selftest()
empty = device.is_cuvette_holder_empty()
first_air = device.first_air_measurement()
first_sample = device.first_sample_measurement()

device.close()
```

See also [Python Low-Level API](./python-low-level.md).

### 4.5 Python High-Level API

In the high-level Python API, create the run with `device="SIMULATION"`:

```python
from hse.evifluor.run import Run

run = Run(
    nr_of_std_low=2,
    nr_of_std_high=2,
    concentration=10.0,
    device="SIMULATION",
)

if not run.check_empty():
    raise RuntimeError("Cuvette holder must be empty before the measurement")

run.measure()
run.measure("std high 1")
run.close()
```

See also [Python High-Level API](./python-high-level.md).

### 4.6 Python CLI

The Python CLI can run against the simulator with `--device SIMULATION`.

Example:

```powershell
python -m hse.evifluor --device SIMULATION info
python -m hse.evifluor --device SIMULATION selftest --json
python -m hse.evifluor --device SIMULATION checkempty
python -m hse.evifluor --device SIMULATION run init 2 2 10
python -m hse.evifluor --device SIMULATION run measure
python -m hse.evifluor --device SIMULATION run measure "std high 1"
```

See also [Python Command Line Interface](./python-cli.md).

### 4.7 Python REST API

First start the REST server:

```powershell
evifluor-rest --host 127.0.0.1 --port 8000
```

Then initialize a run against the simulator by using `device_id: "SIMULATION"`:

```python
from hse.evifluor.rest_client import RestClient

client = RestClient(base_url="http://127.0.0.1:8000", serial_number="SIMULATION")

run = client.run_init(
    nr_of_std_low=2,
    nr_of_std_high=2,
    concentration=10.0,
)
run_id = run["run_id"]

if not client.checkempty()["empty"]:
    raise RuntimeError("Cuvette holder must be empty before the measurement")

client.run_measure(run_id)
client.run_measure(run_id, "std high 1")
```

See also [Python REST API](./python-rest.md).

## 5. Simulator Control Commands

The simulator accepts control commands while it is running.
These commands are useful for test setup and for switching specific states.

Examples:

```powershell
hse-simulator sim RESET
hse-simulator sim CHECKEMPTY 1
hse-simulator sim CHECKEMPTY 0
hse-simulator sim LOAD .\test\testdata\evifluor-P10006-2025_04_24_16_18_09.json
hse-simulator sim NO_AIR 1
hse-simulator sim NO_AIR 0
```

Typical command usage:

- `RESET`: resets the simulator state
- `CHECKEMPTY 1`: report that the cuvette holder is empty
- `CHECKEMPTY 0`: report that the cuvette holder is not empty
- `LOAD <file>`: load measurement data from a JSON file
- `NO_AIR 1`: enable the no-air workflow
- `NO_AIR 0`: disable the no-air workflow

## 6. Command Reference

This chapter summarizes the most important simulator control functions.
All commands are sent with `hse-simulator sim ...` while the simulator is running.

### 6.1 `LOAD <file>`

Loads measurement data from a JSON file into the simulator.
The loaded values are then returned step by step during the following measurement calls.
The file is loaded from the simulator process point of view.
This means the referenced file path must be accessible on the same computer where the simulator is running.
As a consequence, the web UI or CLI that triggers `LOAD` must be used against a simulator running on a machine that can access that file locally.
`LOAD` also depends on the current `NO_AIR` setting of the simulator.
If the simulator is in no-air mode, the loaded file is interpreted as a no-air run.
The client must then also use a no-air run configuration, otherwise the expected measurement order does not match.

Example:

```powershell
hse-simulator sim LOAD .\test\testdata\evifluor-P10006-2025_04_24_16_18_09.json
```

Typical use:

- replay a known measurement run
- reproduce a customer issue with fixed data
- validate a client implementation against stable expected values
- replay a no-air run together with a matching client-side no-air workflow

### 6.2 `RESET`

Resets the simulator state.
This clears loaded measurement progress, resets the empty state to default, and clears temporary simulator status.

Example:

```powershell
hse-simulator sim RESET
```

Typical use:

- start a test from a clean simulator state
- restart a workflow after a failed test run

### 6.3 `CHECKEMPTY 0|1`

Sets the reported cuvette-holder state.

Examples:

```powershell
hse-simulator sim CHECKEMPTY 1
hse-simulator sim CHECKEMPTY 0
```

Meaning:

- `CHECKEMPTY 1`: the simulator reports that the cuvette holder is empty
- `CHECKEMPTY 0`: the simulator reports that the cuvette holder is not empty

Typical use:

- test empty-check handling in a client
- simulate a blocked or occupied cuvette position

### 6.4 `NO_AIR 0|1`

Enables or disables the no-air workflow in the simulator.

Examples:

```powershell
hse-simulator sim NO_AIR 1
hse-simulator sim NO_AIR 0
```

Meaning:

- `NO_AIR 1`: sample-only workflow
- `NO_AIR 0`: normal workflow with air measurements

Typical use:

- validate integrations that use `no_air=True`
- switch between both supported workflow variants

### 6.5 `EXIT`

Stops the running simulator.

Example:

```powershell
hse-simulator sim EXIT
```

Typical use:

- stop the simulator from a script
- terminate a remote or background simulator session cleanly

### 6.6 `ZERO 0|1`

Enables or disables zero-value measurement mode.

Example:

```powershell
hse-simulator sim ZERO 1
```

Typical use:

- test client behavior with degenerate or placeholder measurement values

### 6.7 `SKIP <count>`

Skips the next `<count>` preloaded measurement entries from the currently loaded data set.

Example:

```powershell
hse-simulator sim SKIP 2
```

Typical use:

- continue replay at a later point in a loaded run
- align the simulator state with a partially executed workflow

## 7. Typical Development Workflow

1. Start the simulator with `hse-simulator evifluor`.
2. Optionally preload test data with a JSON file or `LOAD`.
3. Start the client application or script with `Device("SIMULATION")`.
4. Use the web UI or `hse-simulator sim ...` commands to adjust simulator state as needed.
5. Run the normal measurement workflow against the simulator.
