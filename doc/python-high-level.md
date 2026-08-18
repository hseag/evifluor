# Python High-Level API

## 1. Scope

This chapter describes the high-level Python API based on the [`Run`][run-api] class.
It is intended for applications that want a guided measurement workflow instead of manually controlling each low-level step.

## 2. Overview

[`Run`][run-api] wraps the repeated measurement sequence and manages:

- device access
- measurement state
- standard handling
- result recalculation
- persistence of measurement data
- optional persistence of run state

Import path:

```python
from hse.evifluor.run import Run
```

[`Run`][run-api] is the recommended API when the application wants to execute a standard workflow with minimal boilerplate.

## 3. Typical High-Level Example

The following example demonstrates a complete high-level workflow:

```python
from hse.evifluor.run import Run


def main():
    run = Run(nr_of_std_low=1, nr_of_std_high=1, concentration=10.0)

    try:
        sample_order = [
            "std high 1",
            "std low 1",
            "sample 1",
            "sample 2",
        ]

        for sample_name in sample_order:
            # The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
            if not run.check_empty():
                raise RuntimeError("Cuvette holder must be empty before the measurement")

            # Move the empty cuvette into the cuvette guide and start the air measurement.
            run.measure()
            # Dispense 10 µl sample into the cuvette and start the sample measurement.
            run.measure(sample_name)
            # Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.

        run.export_as_csv()
    finally:
        run.close()


if __name__ == "__main__":
    main()
```

## 4. When to Use `Run`

Use [`Run`][run-api] when:

- you want a guided measurement workflow
- you want automatic recalculation after standards are available
- you want automatic persistence after each step
- you want a simple API surface for a liquid-handler workflow
- you want to resume an interrupted workflow from saved state

Use the low-level API instead when:

- you need full control over each device command
- you want to manage air and sample steps explicitly
- you need custom sequencing beyond the built-in state machine

See also:

- [Python Low-Level API](./python-low-level.md)

## 5. Constructor

Create a new run with:

```python
run = Run(
    nr_of_std_low=8,
    nr_of_std_high=8,
    concentration=10.0,
)
```

Important constructor arguments:

- `nr_of_std_low`: number of low-standard measurements used to derive factors
- `nr_of_std_high`: number of high-standard measurements used to derive factors
- `concentration`: target concentration assigned to the high standard
- `path`: optional directory for the measurement file
- `filename`: optional measurement JSON file name
- `device`: optional serial number, `"SIMULATION"`, or an existing `Device` instance
- `kit`: optional kit object, for example `evifluor.kits.Default()` or `evifluor.kits.QubitTM_1X_dsDNA_Broad_Range_BR()`
- `settling_time`: optional override in seconds for the wait time before sample measurements

Behavior:

- if no filename is given, a timestamped JSON filename is generated
- the [`Run`][run-api] instance creates a [`StorageMeasurement`][storage-api] internally
- if no `settling_time` is given, the selected kit provides the default wait time
- after enough standards are available, factors are calculated automatically
- stored measurements without results are recalculated automatically

For predefined kits, string names, fit models, and JSON serialization, see [Kit Reference](./kit.md), especially section 2.

## 6. Run State Model

By default, [`Run`][run-api] keeps an internal state machine:

1. first air setup
2. first sample setup
3. air
4. sample

Each call to [`run.measure(...)`][run-measure-api] advances the workflow by one step.

Practical effect:

- the first call performs the initial air setup
- the second call performs the initial sample setup and stores the first measurement
- subsequent calls alternate between air and sample

If the run is created with `no_air=True`, the workflow skips the air steps and uses a reduced state machine:

1. first sample setup
2. sample

Practical effect with `no_air=True`:

- the first call performs the initial sample setup and stores the first measurement
- all following calls perform sample measurements only
- no intermediate air measurements are taken between samples

## 7. Standard Handling and Recalculation

[`Run`][run-api] derives correction factors automatically once enough low and high standards are available.

Behavior:

- until the configured standard counts are completed, stored measurements may not yet contain calculated results
- once the configured standards are available, factors are calculated
- all stored measurements without results are updated automatically

The intended measurement order is:

1. all `std high` measurements
2. all `std low` measurements
3. all sample measurements

## 8. Persisted Files

[`Run`][run-api] manages a measurement JSON file.

The measurement JSON file contains:

- completed measurements
- optional calculated results
- optional comments, logging, and verification data

You can also persist the workflow state separately with [`run.save_state()`][run-save-api].
This stores the current state machine position, temporary measurement data, factors, the active measurement filename, the selected kit, and the active `settling_time`.

## 9. Checking the Cuvette Holder

Use [`run.check_empty()`][run-checkempty-api]:

```python
empty = run.check_empty()
```

This forwards to the underlying device and returns `True` when the cuvette holder is empty.

## 10. Exporting Data

Export the active measurement file as CSV with [`run.export_as_csv()`][run-export-api]:

```python
run.export_as_csv()
```

## 11. Saving and Loading Run State

Persist the workflow state with [`run.save_state()`][run-save-api]:

```python
run.save_state()
```

Reload it later with [`Run.load_state(...)`][run-load-api]:

```python
run = Run.load_state("evifluor-SN0010-state.json")
```

This is useful when a workflow should be resumed after an interruption without losing the current step and accumulated data.

## 12. Closing the Device

If the `Run` instance owns the device connection, close it when the workflow is finished:

```python
run.close()
```

## 13. Notes

The current `Run` implementation in `evifluor` focuses on guided acquisition, persistence, and resumable workflow state.
It additionally exposes `save_state` and `load_state`, which are useful for longer-running automation scenarios.

[run-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run
[storage-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement
[run-measure-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run.measure
[run-checkempty-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run.check_empty
[run-export-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run.export_as_csv
[run-save-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run.save_state
[run-load-api]: https://hseag.github.io/evifluor/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run.load_state
