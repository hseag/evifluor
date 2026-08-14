# Kit Reference

## 1. Overview

`Kit` objects define how an eviFluor measurement is converted into a concentration after standard-based calibration.

A kit contains:

- a fit algorithm
- the fit parameters `k1`, `k2`, `k3`
- a default `settling time` in seconds
- an optional `stdHighTargetSignalFactor` for the first-sample auto-gain
- a human-readable description

The same kit model is used in the Python and C# implementations and in the C `run` workflow.

## 2. Predefined Kits

If you need to pass a kit name as a string, for example in the Python CLI, Python REST API, or C CLI `run init`, use the value from the `Use this name` column:

| Use this name | Also accepted | Python class | C# class | Behavior |
|---|---|---|---|---|
| `Default` | `default` | `hse.evifluor.kits.Default` | `Hse.EviFluor.Kits.Default` | Linear fit with `k1=1.0`, `k2=0.0`, `k3=0.0` |
| `QubitTM_1X_dsDNA_High_Sensitivity_HS` | `qubit_hs` | `hse.evifluor.kits.QubitTM_1X_dsDNA_High_Sensitivity_HS` | `Hse.EviFluor.Kits.QubitTM_1X_dsDNA_High_Sensitivity_HS` | Linear preset for the Qubit 1X dsDNA High Sensitivity assay |
| `QubitTM_1X_dsDNA_Broad_Range_BR` | `qubit_br` | `hse.evifluor.kits.QubitTM_1X_dsDNA_Broad_Range_BR` | `Hse.EviFluor.Kits.QubitTM_1X_dsDNA_Broad_Range_BR` | HillFit preset for the Qubit 1X dsDNA Broad Range assay |

Copy-and-paste examples:

```bash
python -m hse.evifluor run init 1 1 10 --kit Default
python -m hse.evifluor run init 1 1 10 --kit QubitTM_1X_dsDNA_High_Sensitivity_HS
python -m hse.evifluor run init 1 1 10 --kit QubitTM_1X_dsDNA_Broad_Range_BR
evifluor-cli run init 1 1 10 --kit=Default
evifluor-cli run init 1 1 10 --kit=QubitTM_1X_dsDNA_High_Sensitivity_HS
evifluor-cli run init 1 1 10 --kit=QubitTM_1X_dsDNA_Broad_Range_BR
```

## 3. Fit Algorithms

The configurable `Default` kit supports these fit algorithms:

- `Linear`
  Formula: `k1 * x + k2`
  Here `x` is the linearly interpolated concentration between `std low` and `std high`.

- `LookupTable`
  Uses a lookup-table interpolation on the normalized measured signal.

  The implementation first computes the normalized signal position

  `rfu_norm = (rfu - std_low.value) / (std_high.value - std_low.value)`

  and then interpolates between the neighboring lookup-table entries:

  `concentration = lower.concentration + fraction * (upper.concentration - lower.concentration)`

  with

  `fraction = (rfu_norm - lower.signal) / (upper.signal - lower.signal)`

  Finally the same linear post-scaling as in the `Linear` fit is applied:

  `k1 * concentration + k2`

Notes:

- `k3` is still part of the configurable kit JSON and constructors for compatibility, but it is currently only unused for the implemented `Linear` and `LookupTable` algorithms.
- The lookup table must contain at least one entry. With exactly one entry, that entry's concentration is returned directly.
- Lookup-table signal values must be strictly monotonic. Otherwise the interpolation is invalid.

## 4. CSV Lookup-Table Format

CSV lookup-table files are used to define a custom lookup table for the `LookupTable` fit algorithm.

Expected columns:

- `Comment`
- `RFU`
- `Concentration`

Only `RFU` and `Concentration` are evaluated by the loaders. The `Comment` column is optional from a semantic perspective and is typically used for labels such as sample positions or standard names.

Important conventions:

- The first data row must be the `std high` reference.
- The second data row must be the `std low` reference.
- All following rows are converted into lookup-table entries.

The normalized lookup-table signal is derived from the `RFU` values as

`signal = (rfu - rfu_std_low) / (rfu_std_high - rfu_std_low)`

where:

- `rfu_std_high` is the `RFU` value from the first data row
- `rfu_std_low` is the `RFU` value from the second data row

Additional notes:

- The file must contain at least two data rows so that normalization can be derived.
- `rfu_std_high` and `rfu_std_low` must be different.
- The resulting lookup-table entries are sorted by normalized `signal`.

Example (used for the Qubit 1X dsDNA broad-range assay):

```csv
Comment;RFU;Concentration
Std_High-0_0_0;877.4062425;100
Std_Low-0_0_0;10.895199999999999;0
Sample@C1-0_0_0;15.671000000000001;0.655
Sample@D1-0_0_0;21.377000000000002;1.15
Sample@A2-0_0_0;112.24359999999999;10.3
Sample@B2-0_0_0;395.4468;42.9
Sample@C2-0_0_0;754.7148;80.5
Sample@D2-0_0_0;902.7252000000001;101
Sample@A3-0_0_0;1306.5642;166
Sample@B3-0_0_0;1689.1786;242
```

## 5. Factory Usage

Python:

```python
from hse.evifluor.kits import Default

kit = Default.factory("default")
kit = Default.factory("qubit_hs")
kit = Default.factory("qubit_br")
```

C#:

```csharp
using Hse.EviFluor.Kits;

var kit = Default.Factory("default");
kit = Default.Factory("qubit_hs");
kit = Default.Factory("qubit_br");
```

## 6. Direct Construction

Python:

```python
from hse.evifluor.kits import Default, FitAlgorithm

kit = Default(
    fit_algorithm=FitAlgorithm.Linear,
    settling_time=0.0,
    description="Custom linear kit",
)
```

C#:

```csharp
using Hse.EviFluor.Kits;

var kit = new Default(
    fitAlgorithm: FitAlgorithm.Linear,
    settlingTime: 0.0,
    description: "Custom linear kit");
```

## 7. Run Integration

High-level runs accept a kit plus an optional settling-time override:

- Python: `Run(..., kit=..., settling_time=...)`
- C#: `Run(..., kit: ..., settlingTime: ...)`
- C CLI: `evifluor-cli run init ... --kit=... [--settling-time=...]`

If no explicit settling-time override is given, the run uses the default settling time stored in the selected kit.

## 8. JSON Representation

Serialized kit objects use these fields:

- `fitAlgorithm`
- `k1`
- `k2`
- `k3`
- `lookupTable`
- `settlingTime`
- `stdHighTargetSignalFactor`
- `description`

This representation is used in persisted run state and in the Python REST responses.
