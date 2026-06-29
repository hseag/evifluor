# Verification Reference

The run and REST APIs expose verification findings as a `verification` array.
Each entry represents one detected issue in the most recently verified measurement step.

## Structure

Example:

```json
[
  {
    "problem_id": 2,
    "description": "CUVETTE_MISSING",
    "data": {
      "dark": 12.0,
      "value": 18.0,
      "led_power": 140
    }
  }
]
```

Fields:

- `problem_id`: stable numeric identifier of the verification problem
- `description`: symbolic name of the verification problem
- `data`: serialized object associated with the problem, for example a measurement, auto-gain result, or calculated result

An empty `verification` array means no problems were detected for that step.

## Problem Types

### `SATURATION` (`problem_id = 1`)

Meaning:

- the measured signal reached or exceeded the configured maximum signal threshold

Typical causes:

- sample concentration is too high
- optical signal is too strong
- the current measurement is outside the intended operating range

Attached `data`:

- the offending single measurement

### `CUVETTE_MISSING` (`problem_id = 2`)

Meaning:

- the measured signal does not match the expected presence of a cuvette

Typical causes:

- no cuvette was inserted
- the cuvette is misplaced
- the sample holder is empty although the workflow expected a cuvette

Attached `data`:

- the single measurement that failed the cuvette presence check

### `MIN_LED_POWER` (`problem_id = 3`)

Meaning:

- reserved verification problem identifier for LED power being too low

Current status:

- defined by the API but currently not emitted by the Python verification logic

### `MAX_LED_POWER` (`problem_id = 4`)

Meaning:

- reserved verification problem identifier for LED power being too high

Current status:

- defined by the API but currently not emitted by the Python verification logic

### `AUTO_GAIN_RESULT` (`problem_id = 5`)

Meaning:

- the first-sample auto-gain procedure did not report a valid result

Typical causes:

- auto-gain could not find a suitable operating point
- the optical conditions did not allow a valid first-sample setup

Attached `data`:

- the auto-gain result object

### `WRONG_LEVEL` (`problem_id = 6`)

Meaning:

- the first sample of the `standard high` sequence is outside the expected target signal window

Typical causes:

- the inserted standard does not match the configured workflow
- the measured standard level is too low or too high
- there is an issue with preparation, placement, or signal quality

Attached `data`:

- the measured first-sample single measurement

### `NEGATIVE_CONCENTRATION` (`problem_id = 7`)

Meaning:

- the calculated concentration is below the configured negative-concentration threshold

Typical causes:

- noisy or inconsistent standard/sample values
- baseline and sample values produce a physically implausible result
- the sample is effectively below the calibrated range

Attached `data`:

- the calculated result object

## Notes

- Verification is step-based. The `verification` array in the REST run snapshot describes the most recently executed step, not the entire run history.
- Multiple problems can be reported for one step.
- Duplicate problem types are suppressed within a single verification result.
