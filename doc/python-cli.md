# Python Command Line Interface

## 1. Scope

This chapter documents the Python command line tool only.
It does not describe the in-process high-level or low-level Python APIs.

## 2. Overview

The Python interface can also be used through the command line entry point.
This tool provides access to common device operations and the guided run workflow without embedding the library in application code.

General syntax:

```text
evifluor [OPTIONS] COMMAND [ARGUMENTS]
python -m hse.evifluor [OPTIONS] COMMAND [ARGUMENTS]
```

The command line tool is suitable for:

- interactive device inspection
- operational workflows
- scripting
- test and service tasks

The currently implemented command set includes:

- `info`
- `selftest`
- `checkempty`
- `run`

## 3. Installation and Startup

Entry points:

```bash
evifluor --help
python -m hse.evifluor --help
```

This chapter focuses on usage after the tool is available in the Python environment.

## 4. Command Syntax

Global options:

- `--device DEVICE` selects a specific device serial number
- `--debug` prints the full traceback on errors

Example:

```text
python -m hse.evifluor --device SN0010 selftest
```

## 5. Main Commands

### 5.1 `info`

Shows device information.

```text
python -m hse.evifluor info
python -m hse.evifluor info --json
```

Behavior:

- default output prints serial number, firmware version, and production number
- `--json` prints the same information as formatted JSON

### 5.2 `selftest`

Runs the device self-test.

```text
python -m hse.evifluor selftest
python -m hse.evifluor selftest --json
python -m hse.evifluor selftest --file selftest.txt
```

Behavior:

- default output prints `selftest: OK` or `selftest: FAILED`
- `--json` prints the self-test result as JSON
- `--file FILE` writes the output to a file instead of stdout
- the command returns exit code `0` when the self-test succeeds and `1` when problems are reported

### 5.3 `checkempty`

Checks whether the cuvette holder is empty.

```text
python -m hse.evifluor checkempty
```

It prints:

- `Empty` if the cuvette holder is empty
- `Not empty` otherwise

The command returns exit code `0` for `Empty` and `1` for `Not empty`.

### 5.4 `run`

Performs a guided workflow on top of the Python `Run` implementation.

Supported forms:

```text
python -m hse.evifluor run [OPTIONS] init NR_OF_STD_LOW NR_OF_STD_HIGH CONCENTRATION
python -m hse.evifluor run [OPTIONS] measure [COMMENT]
python -m hse.evifluor run [OPTIONS] export
```

Run options:

- `--working-dir DIR`
- `--file FILE`
- `--kit NAME` for `run init` only, default `Default`
- `--settling_time SECONDS` for `run init` only, optional
- `--no-air` for `run init` only

Behavior:

- `init` initializes a run state and selects the measurement file
- `init --kit NAME` selects the predefined kit preset used for result calculation and timing
- `init --settling_time SECONDS` overrides the kit-specific wait time before sample measurements
- `init --no-air` initializes a run that skips air measurements and stores sample-only entries
- `measure` advances the workflow state machine by one step
- `export` creates a CSV file from the active run JSON file

Supported kit names are listed in [Kit Reference](./kit.md), section 2.

## 6. Output and Files

The Python CLI uses:

- plain text output for operational commands
- JSON output for `info --json` and `selftest --json`
- JSON files for persisted run data
- CSV files for exported run data
- a log file named `evifluor.log` in the working directory unless `--debug` is used

## 7. Typical Examples

Query device information:

```text
python -m hse.evifluor info
python -m hse.evifluor info --json
```

Run a self-test:

```text
python -m hse.evifluor selftest --json
```

Check the cuvette holder state:

```text
python -m hse.evifluor checkempty
```

Initialize and use a guided run:

```bash
python -m hse.evifluor run init 1 1 10 --kit Default
# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Move the empty cuvette into the cuvette guide and start the air measurement.
python -m hse.evifluor run measure
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "std high 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Move the empty cuvette into the cuvette guide and start the air measurement.
python -m hse.evifluor run measure
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "std low 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Move the empty cuvette into the cuvette guide and start the air measurement.
python -m hse.evifluor run measure
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "sample 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Move the empty cuvette into the cuvette guide and start the air measurement.
python -m hse.evifluor run measure
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "sample 2"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
python -m hse.evifluor run export
```

Initialize a run with a different predefined kit:

```bash
python -m hse.evifluor run init 1 1 10 --kit qubit_br
```

Initialize a run with an explicit settling time override:

```bash
python -m hse.evifluor run init 1 1 10 --settling_time 0.0
```

Initialize and use a guided no-air run:

```bash
python -m hse.evifluor run init 1 1 10 --no-air
# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "std high 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "std low 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "sample 1"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

# The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
python -m hse.evifluor checkempty
# Dispense the liquid into the cuvette and start the sample measurement.
python -m hse.evifluor run measure "sample 2"
# Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
python -m hse.evifluor run export
```

## 8. Notes

The Python CLI is intentionally focused on common operational workflows.
For direct library integration, use the Python high-level or low-level APIs instead.

API links:

- [`hse.evifluor.cli`][cli-api]
- [`hse.evifluor.__main__`][main-api]

[cli-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.cli.html
[main-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/modules.html
