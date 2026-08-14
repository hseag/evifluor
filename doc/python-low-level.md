# Python Low-Level API

## 1. Scope

This chapter describes the low-level Python API.
It intentionally does not use the [`Run`][run-api] class, because the goal is to show the explicit device workflow.

## 2. API Overview

The low-level Python API is centered around explicit interaction with a [`Device`][device-api] object and the related measurement and storage classes.

Main objects to document:

- [`Device`][device-api]
- [`SingleMeasurement`][singlemeasurement-api]
- [`Measurement`][measurement-api]
- [`StorageMeasurement`][storage-api]

Import path:

```python
from hse.evifluor.device import Device
from hse.evifluor.measurement import Measurement
from hse.evifluor.storage import StorageMeasurement
```

Important low-level [`Device`][device-api] methods:

- [`Device(device=None)`][device-api] opens a physical device
- [`Device.find_device()`][device-finddevice-api] searches for connected devices
- [`Device.serial_number()`][device-serial-api]
- [`Device.firmware_version()`][device-fw-api]
- [`Device.production_number()`][device-prod-api]
- [`Device.selftest()`][device-selftest-api]
- [`Device.is_cuvette_holder_empty()`][device-empty-api]
- [`Device.baseline()`][device-baseline-api]
- [`Device.measure()`][device-measure-api]
- [`Device.first_air_measurement()`][device-firstair-api]
- [`Device.first_sample_measurement()`][device-firstsample-api]
- [`Device.logging()`][device-logging-api]
- [`Device.close()`][device-close-api]

## 3. Complete Low-Level Example

The following example demonstrates the full low-level workflow without [`Run`][run-api]:

```python
from hse.evifluor.device import Device
from hse.evifluor.measurement import Measurement
from hse.evifluor.storage import StorageMeasurement


def acquire_first_measurement(device):
    # The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
    if not device.is_cuvette_holder_empty():
        raise RuntimeError("Cuvette holder is not empty")

    # Move the empty cuvette into the cuvette guide and start the first air measurement.
    air = device.first_air_measurement()
    # Dispense the liquid into the cuvette and start the first sample measurement.
    sample = device.first_sample_measurement()
    # Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
    return Measurement(air, sample)


def acquire_follow_up_measurement(device):
    # The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
    if not device.is_cuvette_holder_empty():
        raise RuntimeError("Cuvette holder is not empty")

    # Move the empty cuvette into the cuvette guide and start the air measurement.
    air = device.measure()
    # Dispense the liquid into the cuvette and start the sample measurement.
    sample = device.measure()
    # Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
    return Measurement(air, sample)


def main():
    device = Device()

    try:
        storage = StorageMeasurement()
        storage.add_device_info(device, "low-level example")

        print("serial:", device.serial_number())
        print("firmware:", device.firmware_version())

        selftest = device.selftest()
        if selftest.has_problems():
            raise RuntimeError(f"Selftest failed with code {selftest.result}")

        std_high = [
            acquire_first_measurement(device),
        ]
        std_low = [
            acquire_follow_up_measurement(device),
        ]
        samples = [
            acquire_follow_up_measurement(device),
            acquire_follow_up_measurement(device),
        ]

        factors = Measurement.calculate_factors(0.0, 10.0, std_low, std_high)

        for name, measurement in [
            ("std high 1", std_high[0]),
            ("std low 1", std_low[0]),
            ("sample 1", samples[0]),
            ("sample 2", samples[1]),
        ]:
            storage.append_with_results(
                measurement,
                measurement.results(factors),
                name,
                logging=device.logging(),
            )

        storage.save("run_data.json")
        StorageMeasurement.export_as_csv("run_data.json")
    finally:
        device.close()


if __name__ == "__main__":
    main()
```

This example uses two high standards, two low standards, and two samples for clarity.
The same pattern scales directly to other counts: first collect all `std high` measurements, then all `std low` measurements, then the samples, while keeping the low-level sequence `first_air_measurement()`, `first_sample_measurement()`, and then repeated `measure()` / `measure()` pairs.

## 4. Opening a Device

You can either let the library auto-detect a connected device or pass a specific serial number.

Examples:

```python
device = Device()
device = Device("SN0010")
```

Notes:

- [`Device()`][device-api] searches for a connected device with the expected VID and PID
- when a device cannot be found, the constructor raises an exception
- `Device("SIMULATION")` connects to the TCP simulator instead of a physical serial device

## 5. Querying Device Information

Use these methods for basic metadata:

```python
device = Device()

serial_number = device.serial_number()
firmware_version = device.firmware_version()
production_number = device.production_number()
```

Typical uses:

- identify the device in logs and stored files
- display firmware information in a UI or CLI
- add device metadata to persisted measurement data

## 6. Running a Self-Test

Run the self-test with [`device.selftest()`][device-selftest-api]:

```python
result = device.selftest()
```

The returned [`SelfttestResult`][selftest-api] object provides:

- [`result.result`][selftest-result-api]
- [`result.has_problems()`][selftest-hasproblems-api]
- [`result.has_communication_error()`][selftest-hascommunicationerror-api]

Example:

```python
result = device.selftest()
if result.has_problems():
    raise RuntimeError(f"Selftest failed with code {result.result}")
```

If you need a broader device-side payload, use:

```python
report = device.technical_report()
```

## 7. Acquiring Raw Measurements

The low-level fluorescence workflow is explicit:

1. call [`first_air_measurement()`][device-firstair-api] for the initial air reference
2. call [`first_sample_measurement()`][device-firstsample-api] for the initial sample and auto-gain step
3. call [`measure()`][device-measure-api] / [`measure()`][device-measure-api] pairs for all following measurements

Example for the first standard:

```python
# Move the empty cuvette into the cuvette guide and start the first air measurement.
first_air = device.first_air_measurement()
# Dispense the liquid into the cuvette and start the first sample measurement.
first_sample = device.first_sample_measurement()
measurement = Measurement(first_air, first_sample)
```

Example for a following standard or sample:

```python
# Move the empty cuvette into the cuvette guide and start the air measurement.
air = device.measure()
# Dispense the liquid into the cuvette and start the sample measurement.
sample = device.measure()
measurement = Measurement(air, sample)
```

You can also check the cuvette guide state before starting:

```python
empty = device.is_cuvette_holder_empty()
```

The [`baseline()`][device-baseline-api] method is also available and clears the device's internal recent-measurement buffer, but it is not part of the normal guided fluorescence workflow shown here.

## 8. Building a `Measurement`

Create a [`Measurement`][measurement-api] from either:

- a [`FirstAirMeasurementResult`][firstair-api] and a [`FirstSampleMeasurementResult`][firstsample-api], or
- two [`SingleMeasurement`][singlemeasurement-api] instances for air and sample

Examples:

```python
measurement = Measurement(first_air, first_sample, comment="std high 1")
measurement = Measurement(air, sample, comment="sample 1")
```

For the no-air workflow, a measurement can also be built without a separate air value:

```python
measurement = Measurement(None, first_sample, comment="std high 1")
```

## 9. Calculating Results

Calculate fluorescence calibration factors with [`Measurement.calculate_factors(...)`][measurement-calculatefactors-api]:

```python
factors = Measurement.calculate_factors(0.0, 10.0, std_low_measurements, std_high_measurements)
```

Then calculate sample concentrations with [`measurement.results(...)`][measurement-results-api]:

```python
results = measurement.results(factors)
```

Notes:

- the standard order must be `std high` first, then `std low`
- the concentration of `std low` is typically `0.0`
- the concentration of `std high` depends on the used assay kit; see [Kit Reference](./kit.md), section 2
- the default calculation uses linear interpolation between the two standard levels

If you need a different fitting model, pass a different kit object to [`measurement.results(...)`][measurement-results-api]. The available presets and configurable fit models are described in [Kit Reference](./kit.md).

## 10. Persisting Data

Use [`StorageMeasurement`][storage-api] for JSON persistence:

```python
storage = StorageMeasurement()
storage.add_device_info(device, comment="manual low-level workflow")
storage.append_with_results(measurement, results, comment="sample 1", logging=device.logging())
storage.save("run_data.json")
```

Available operations include:

- [`StorageMeasurement()`][storage-api] to create a new container
- [`StorageMeasurement(filename)`][storage-api] to load an existing JSON file
- [`add_device_info(device, comment=None)`][storage-adddeviceinfo-api]
- `append(...)`
- [`append_with_results(...)`][storage-appendwithresults-api]
- [`save(filename)`][storage-save-api]
- [`StorageMeasurement.export_as_csv(filename_json)`][storage-exportcsv-api]

CSV export example:

```python
StorageMeasurement.export_as_csv("run_data.json")
```

In no-air data sets, the CSV export leaves the `air` columns empty.

## 11. Error Handling and Cleanup

The Python API uses exceptions for device communication and data errors.

Handle at least these cases:

- device not found
- device communication timeout or protocol error
- self-test failure according to the returned self-test result
- invalid file paths during persistence or export

Example:

```python
try:
    device = Device()
    result = device.selftest()
    if result.has_problems():
        raise RuntimeError(f"Selftest failed with code {result.result}")
finally:
    device.close()
```

Cleanup note:

- for physical devices the serial port is held inside the `Device` instance
- call [`device.close()`][device-close-api] when the workflow is complete

## 12. Notes About `Run`

The [`Run`][run-api] class is intentionally excluded from this chapter because it abstracts away the individual device operations.

[run-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.run.html#hse.evifluor.run.Run
[device-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device
[singlemeasurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.singlemeasurement.html#hse.evifluor.singlemeasurement.SingleMeasurement
[measurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.measurement.html#hse.evifluor.measurement.Measurement
[storage-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement
[selftest-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.SelfttestResult
[firstair-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.FirstAirMeasurementResult
[firstsample-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.FirstSampleMeasurementResult
[device-finddevice-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.find_device
[device-serial-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.serial_number
[device-fw-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.firmware_version
[device-prod-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.production_number
[device-selftest-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.selftest
[device-empty-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.is_cuvette_holder_empty
[device-baseline-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.baseline
[device-measure-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.measure
[device-firstair-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.first_air_measurement
[device-firstsample-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.first_sample_measurement
[device-logging-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.logging
[device-close-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.Device.close
[selftest-result-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.SelfttestResult.result
[selftest-hasproblems-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.SelfttestResult.has_problems
[selftest-hascommunicationerror-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.device.html#hse.evifluor.device.SelfttestResult.has_communication_error
[measurement-calculatefactors-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.measurement.html#hse.evifluor.measurement.Measurement.calculate_factors
[measurement-results-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.measurement.html#hse.evifluor.measurement.Measurement.results
[storage-adddeviceinfo-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement.add_device_info
[storage-appendwithresults-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement.append_with_results
[storage-save-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement.save
[storage-exportcsv-api]: https://hseag.github.io/evi-test/pre-release/doc/api/python/hse.evifluor.storage.html#hse.evifluor.storage.StorageMeasurement.export_as_csv
