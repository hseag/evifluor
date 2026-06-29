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
| `QubitTM_1X_dsDNA_Broad_Range_BR` | `qubit_br` | `hse.evifluor.kits.QubitTM_1X_dsDNA_Broad_Range_BR` | `Hse.EviFluor.Kits.QubitTM_1X_dsDNA_Broad_Range_BR` | Power preset for the Qubit 1X dsDNA Broad Range assay |

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

- `Power`
  Formula: `k1 * x^k2`
  Negative interpolated values are clamped to `0.0`

- `Quadratic`
  Formula: `k1 * x^2 + k2 * x + k3`
  Negative interpolated values are clamped to `0.0`

`x` is the linearly interpolated concentration between `std low` and `std high`.

## 4. Factory Usage

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

## 5. Direct Construction

Python:

```python
from hse.evifluor.kits import Default, FitAlgorithm

kit = Default(
    fit_algorithm=FitAlgorithm.Power,
    k1=1.2,
    k2=1.05,
    settling_time=0.0,
    description="Custom power kit",
)
```

C#:

```csharp
using Hse.EviFluor.Kits;

var kit = new Default(
    fitAlgorithm: FitAlgorithm.Power,
    k1: 1.2,
    k2: 1.05,
    settlingTime: 0.0,
    description: "Custom power kit");
```

## 6. Run Integration

High-level runs accept a kit plus an optional settling-time override:

- Python: `Run(..., kit=..., settling_time=...)`
- C#: `Run(..., kit: ..., settlingTime: ...)`
- C CLI: `evifluor-cli run init ... --kit=... [--settling-time=...]`

If no explicit settling-time override is given, the run uses the default settling time stored in the selected kit.

## 7. JSON Representation

Serialized kit objects use these fields:

- `fitAlgorithm`
- `k1`
- `k2`
- `k3`
- `settlingTime`
- `stdHighTargetSignalFactor`
- `description`

This representation is used in persisted run state and in the Python REST responses.
