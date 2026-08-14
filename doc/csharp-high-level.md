# C# High-Level API

## 1. Scope

This chapter describes the high-level C# API based on the [`Run`][run-api] class.
It is intended for applications that want a guided measurement workflow instead of manually controlling each low-level step.

## 2. Overview

[`Run`][run-api] wraps the repeated measurement sequence and manages:

- device access
- measurement state
- standard handling
- result recalculation
- persistence of measurement data

Import path:

```csharp
using Hse.EviFluor;
```

[`Run`][run-api] is the recommended API when the application wants to execute a standard workflow with minimal boilerplate.

## 3. Typical High-Level Example

The following example demonstrates a complete high-level workflow:

```csharp
using System;
using Hse.EviFluor;

internal class Program
{
    private static void Main()
    {
        var run = new Run(nrOfStdLow: 1, nrOfStdHigh: 1, concentration: 10.0);

        string[] samples = [ "std high 1", "std low 1", "sample 1", "sample 2" ];

        foreach (string sample in samples)
        {
            // The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
            if (!run.checkEmpty())
            {
                throw new InvalidOperationException("Cuvette holder must be empty before the measurement");
            }

            // Move the empty cuvette into the cuvette guide and start the air measurement.
            run.measure();
            // Dispense the liquid into the cuvette and start the sample measurement.
            run.measure(sample);
            // Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
        }
    }
}
```

## 4. When to Use `Run`

Use [`Run`][run-api] when:

- you want a guided measurement workflow
- you want automatic recalculation after standards are available
- you want automatic persistence after each step
- you want a simple API surface for a liquid-handler workflow

Use the low-level API instead when:

- you need full control over each device command
- you want to manage air and sample steps explicitly
- you need custom sequencing beyond the built-in state machine

See also:

- [C# Low-Level API](./csharp-low-level.md)

## 5. Constructor

Create a new run with:

```csharp
var run = new Run(
    nrOfStdLow: 8,
    nrOfStdHigh: 8,
    concentration: 10.0);
```

Important constructor arguments:

- `nrOfStdLow`: number of low-standard measurements used to derive factors
- `nrOfStdHigh`: number of high-standard measurements used to derive factors
- `concentration`: target concentration assigned to the high standard
- `path`: optional directory for the measurement file
- `filename`: optional measurement JSON file name
- `device`: optional serial number or `"SIMULATION"`
- `kit`: optional kit object, for example `new Hse.EviFluor.Kits.Default()` or `new Hse.EviFluor.Kits.QubitTM_1X_dsDNA_Broad_Range_BR()`
- `settlingTime`: optional override in seconds for the wait time before sample measurements

Behavior:

- if no filename is given, a timestamped JSON filename is generated
- the [`Run`][run-api] instance creates a [`StorageMeasurement`][storage-measurement-api] internally
- if no `settlingTime` is given, the selected kit provides the default wait time
- after enough standards are available, factors are calculated automatically
- stored measurements without results are recalculated automatically

For predefined kits, string names, fit models, and JSON serialization, see [Kit Reference](./kit.md), especially section 2.

## 6. Run State Model

[`Run`][run-api] keeps an internal state machine:

1. first air setup
2. first sample setup
3. air
4. sample

Each call to [`run.measure(...)`][run-measure-api] advances the workflow by one step.

Practical effect:

- the first call performs the initial air setup
- the second call performs the initial sample setup and stores the first measurement
- subsequent calls alternate between air and sample

## 7. Standard Handling and Recalculation

[`Run`][run-api] derives correction factors automatically once enough low and high standards are available.

Behavior:

- until the configured standard counts are completed, stored measurements may not yet contain calculated results
- once the configured standards are available, factors are calculated
- all stored measurements without results are updated automatically

## 8. Persisted Files

[`Run`][run-api] manages a measurement JSON file.

The measurement JSON file contains:

- completed measurements
- optional calculated results
- optional comments, logging, and verification data

You can also persist and later restore the workflow state with `Run.SaveState(...)` and `Run.LoadState(...)`.
The persisted state includes the selected kit and the active `settlingTime`.

## 9. Checking the Cuvette Holder

Use [`run.checkEmpty()`][run-checkempty-api]:

```csharp
bool empty = run.checkEmpty();
```

This forwards to the underlying device and returns `true` when the cuvette holder is empty.

## 10. Exporting Data

Export the active measurement file as CSV with [`StorageMeasurement.ExportAsCsv(...)`][storage-exportcsv-api] after the run data has been saved.

[run-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Run.html
[storage-measurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.StorageMeasurement.html
[run-measure-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Run.html#Hse_EviFluor_Run_measure_System_String_
[run-checkempty-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Run.html#Hse_EviFluor_Run_checkEmpty
[storage-exportcsv-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.StorageMeasurement.html#Hse_EviFluor_StorageMeasurement_ExportAsCsv_System_String_
