# C Command Line Interface

## 1. Scope

This chapter documents the C command line tool only.
It does not describe a separate low-level C programming API.

## 2. Overview

The C interface is used through the command line executable.
This tool provides access to common device operations without embedding the library in application code.

General syntax:

```text
evifluor-cli [OPTIONS] COMMAND [ARGUMENTS]
```

The command line tool is suitable for:

- interactive device inspection
- operational workflows
- scripting
- test and service tasks

The currently implemented command set includes:

- `baseline`
- `command`
- `data`
- `empty`
- `export`
- `fwupdate`
- `get`
- `help`
- `measure`
- `run`
- `save`
- `selftest`
- `set`
- `version`

## 3. Installation and Build

The C command line tool is built with CMake.
The command line project is intended to be compilable on both Windows and Linux.
A compiled version is available in `/c/dist`.

A typical CMake workflow is:

```text
cmake -S <source-dir> -B <build-dir>
cmake --build <build-dir>
cmake --install <build-dir>
```

The exact generator, compiler, build type, install prefix, and dependency setup depend on the target platform and project environment.

## 4. Command Syntax

Global options:

- `--verbose` prints debug information
- `--help` or `-h` prints help
- `--device DEVICE` selects a specific device
- `--use-checksum` enables protocol mode with checksum

Example:

```text
evifluor-cli --device SN0010 selftest
```

## 5. Main Commands

### 5.1 `version`

Prints the version of the CLI tool.

```text
evifluor-cli version
```

### 5.2 `selftest`

Runs the internal self-test.

```text
evifluor-cli selftest
```

If the result is not OK, a common reason is a blocked optical path or a wrong mechanical state around the cuvette guide.

### 5.3 `empty`

Checks whether the cuvette guide is empty.

```text
evifluor-cli empty
```

It prints:

- `Empty` if the cuvette guide is empty
- `Not empty` otherwise

### 5.4 `baseline`

Clears the firmware's internal storage of the recent measurements.

```text
evifluor-cli baseline
```

This command is typically used before starting a new manual measurement sequence.

### 5.5 `measure`

Performs a measurement and prints the values to stdout.

```text
evifluor-cli measure
evifluor-cli measure --first-air
evifluor-cli measure --first-sample
```

Supported options:

- `--measure`
- `--first-air`
- `--first-sample`

Output formats:

- default measurement: `dark sample ledPower`
- first-air measurement: `min-dark min-sample min-ledPower max-dark max-sample max-ledPower`
- first-sample measurement: `dark sample ledPower autogain-found autogain-ledPower`

The listed value formats describe the successful command output.

### 5.6 `save`

Stores the latest measurement data in a JSON file.

```text
evifluor-cli save [OPTIONS] FILE [COMMENT]
```

Relevant options:

- `--append`
- `--create`
- `--mode-raw`
- `--mode-measurement`

Behavior:

- `--mode-raw` stores all recent measurements as single measurements
- `--mode-measurement` stores air-sample pairs when exactly two recent measurements are available; otherwise the command stores the available measurements as single values
- `COMMENT` is optional and added to the JSON entry

### 5.7 `export`

Exports JSON data to CSV.

```text
evifluor-cli export [OPTIONS] JSON_FILE CSV_FILE
```

Relevant options:

- `--delimiter-comma`
- `--delimiter-semicolon`
- `--delimiter-tab`
- `--mode-raw`
- `--mode-measurement`

### 5.8 `data`

Handles data already stored in JSON files.

Supported subcommands:

- `evifluor-cli data print FILE`
- `evifluor-cli data calculate CONCENTRATION_LOW CONCENTRATION_HIGH NR_OF_SAMPLES_LOW NR_OF_SAMPLES_HIGH FILE`

`data print` prints calculated values from the JSON file.

`data calculate` adds calculated concentration values to the JSON file.

The parameter order for `data calculate` is:

1. low concentration
2. high concentration
3. number of low-standard samples
4. number of high-standard samples
5. JSON file

### 5.9 `get`

Reads a value from the device.

```text
evifluor-cli get INDEX
```

The built-in help currently documents these indices:

- `0`: firmware version
- `1`: serial number
- `3`: production number
- `10`: number of stored measurements
- `15`: LED power
- `16`: LED power minimum
- `17`: LED power maximum

### 5.10 `set`

Writes a value to the device.

```text
evifluor-cli set INDEX VALUE
```

Warning:

- changing device values can damage the device or lead to incorrect results

### 5.11 `command`

Executes a raw device command.

```text
evifluor-cli command "V 0"
```

This command is mainly intended for testing and troubleshooting.

### 5.12 `fwupdate`

Updates the firmware from an SREC file.

```text
evifluor-cli fwupdate firmware.srec
```

### 5.13 `run`

Performs a guided workflow on top of the low-level commands.

Supported forms:

```text
evifluor-cli run [OPTIONS] init NR_STD_LOW NR_STD_HIGH CONCENTRATION [--no-air] [--kit=NAME] [--settling-time=SECONDS]
evifluor-cli run [OPTIONS] measure [COMMENT]
evifluor-cli run [OPTIONS] checkempty
evifluor-cli run [OPTIONS] export
```

Run options:

- `--working-dir=DIR`
- `--file=FILE`
- `--no-air` only with `run init`
- `--kit=NAME` only with `run init`
- `--settling-time=SECONDS` only with `run init`

Behavior:

- `init` creates the run state file and selects the data file
- `init ... --no-air` initializes a sample-only run without separate air measurements, aligned with the Python CLI
- `init ... --kit=...` applies a predefined kit fit model during result calculation
- `init ... --settling-time=...` overrides the settling time stored in the selected kit
- `measure` advances the workflow state machine
- `checkempty` returns exit code `0` when the cuvette guide is empty and exit code `57` when it is not empty
- `export` creates a CSV file next to the active run JSON file

Supported predefined kit names:

- `Default`
- `QubitTM_1X_dsDNA_High_Sensitivity_HS`
- `QubitTM_1X_dsDNA_Broad_Range_BR`
- aliases: `qubit_hs`, `qubit_br`

## 6. Exit Codes

The built-in CLI help currently documents these exit codes:

- `0`: no error
- `1`: unknown command
- `2`: invalid parameter
- `3`: timeout
- `4`: SREC flash write error
- `5`: SREC unsupported type
- `6`: SREC invalid CRC
- `7`: SREC invalid string
- `8`: leveling failed, cuvette holder blocked
- `10`: EviFluor module not found
- `50`: unknown command-line option
- `51`: response error
- `52`: protocol error
- `53`: unknown command-line argument
- `55`: invalid number
- `56`: file not found
- `57`: cuvette guide not empty
- `100`: communication error

## 7. Output Formats

The C CLI uses:

- plain text output for measurement and status commands
- JSON files for persisted measurement data
- CSV files for exported measurement data

The `save` command produces JSON output files.
The `export` command produces CSV output files.
The `run` command produces and updates state and data JSON files.

## 8. Files Produced by the Tool

Typical generated files:

- measurement JSON files created by `save`
- calculated JSON files updated by `data calculate`
- CSV files created by `export`
- run state JSON files created by `run init`

## 9. Typical Examples

Run a self-test:

```text
evifluor-cli selftest
```

Check the cuvette guide state:

```text
evifluor-cli empty
```

Query a device value:

```text
evifluor-cli get 0
```

Perform a manual measurement sequence:

```text
evifluor-cli baseline
evifluor-cli measure --first-air
evifluor-cli measure --first-sample
evifluor-cli save data.json "std high 1"
evifluor-cli empty
evifluor-cli measure
evifluor-cli measure
evifluor-cli save data.json "std low 1"
evifluor-cli empty
evifluor-cli measure
evifluor-cli measure
evifluor-cli save data.json "sample 1"
evifluor-cli empty
evifluor-cli measure
evifluor-cli measure
evifluor-cli save data.json "sample 2"
evifluor-cli data calculate 0 10 2 2 data.json
evifluor-cli export data.json data.csv
```

Initialize and use a guided run:

```text
evifluor-cli run init 1 1 10 --kit=Default
evifluor-cli run checkempty
evifluor-cli run measure
evifluor-cli run measure "std high 1"
evifluor-cli run checkempty
evifluor-cli run measure
evifluor-cli run measure "std low 1"
evifluor-cli run checkempty
evifluor-cli run measure
evifluor-cli run measure "sample 1"
evifluor-cli run checkempty
evifluor-cli run measure
evifluor-cli run measure "sample 2"
evifluor-cli run export
```

Initialize and use a guided run without air measurements:

```text
evifluor-cli run init 1 1 10 --no-air --kit=QubitTM_1X_dsDNA_Broad_Range_BR --settling-time=5
evifluor-cli run checkempty
evifluor-cli run measure "std high 1"
evifluor-cli run checkempty
evifluor-cli run measure "std low 1"
evifluor-cli run checkempty
evifluor-cli run measure "sample 1"
evifluor-cli run checkempty
evifluor-cli run measure "sample 2"
evifluor-cli run export
```

## 10. Limitations

This chapter is intentionally limited to the command line workflow for C.
