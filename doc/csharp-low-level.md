# C# Low-Level API

## 1. Scope

This chapter describes the low-level C# API.
It intentionally does not use the [`Run`][run-api] class, because the goal is to show the explicit device workflow.

## 2. API Overview

The low-level API is centered around explicit interaction with a [`Device`][device-api] object and related data classes.

Main objects to document:

- [`Device`][device-api]
- [`SingleMeasurement`][single-measurement-api]
- [`Measurement`][measurement-api]
- storage-related classes such as [`StorageMeasurement`][storage-measurement-api]

Import path:

```csharp
using Hse.EviFluor;
```

Important low-level [`Device`][device-api] members:

- [`new Device(string? serialNumber = null)`][device-api]
- [`Device.GetAvailableDevices()`][device-getavailabledevices-api]
- [`device.SerialNumber()`][device-serialnumber-api]
- [`device.FirmwareVersion()`][device-firmwareversion-api]
- [`device.ProductionNumber()`][device-productionnumber-api]
- [`device.SelfTest()`][device-selftest-api]
- [`device.IsCuvetteHolderEmpty()`][device-iscuvetteholderempty-api]
- [`device.Baseline()`][device-baseline-api]
- [`device.Measure()`][device-measure-api]
- [`device.Logging()`][device-logging-api]
- `device.Dispose()`

## 3. Complete Low-Level Example

The following example demonstrates the full low-level workflow without [`Run`][run-api]:

```csharp
using System;
using System.Collections.Generic;
using Hse.EviFluor;

internal class Program
{
    private static void Main()
    {
        using var device = new Device();
        var storage = new StorageMeasurement();
        
        Console.WriteLine($"serial: {device.SerialNumber()}");
        Console.WriteLine($"firmware: {device.FirmwareVersion()}");

        SelfTestResult selftest = device.SelfTest();
        if (selftest.HasProblems())
        {
            throw new InvalidOperationException($"Selftest failed with code {selftest.Result}");
        }

        static Measurement AcquireFirstMeasurement(Device device)
        {
            // The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
            if (!device.IsCuvetteHolderEmpty())
            {
                throw new InvalidOperationException("Cuvette holder is not empty");
            }

            // Move the empty cuvette into the cuvette guide and start the first air measurement.
            FirstAirMeasurementResult air = device.FirstAirMeasurement();
            // Dispense the liquid into the cuvette and start the first sample measurement.
            FirstSampleMeasurementResult sample = device.FirstSampleMeasurement();
            // Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
            return new Measurement(air, sample);
        }

        var stdHigh = new List<Measurement>();
        var stdLow = new List<Measurement>();
        var samples = new List<Measurement>();

        stdHigh.Add(AcquireFirstMeasurement(device)); // std high 1

        foreach (int _ in new[] { 0 })
        {
            // The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
            if (!device.IsCuvetteHolderEmpty())
            {
                throw new InvalidOperationException("Cuvette holder is not empty");
            }

            // Move the empty cuvette into the cuvette guide and start the air measurement.
            SingleMeasurement air = device.Measure();
            // Dispense the liquid into the cuvette and start the sample measurement.
            SingleMeasurement sample = device.Measure();
            // Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
            stdLow.Add(new Measurement(air, sample));
        }

        foreach (int _ in new[] { 0, 1 })
        {
            // The liquid handler picks up a cuvette with the tip and moves above the cuvette guide.
            if (!device.IsCuvetteHolderEmpty())
            {
                throw new InvalidOperationException("Cuvette holder is not empty");
            }

            // Move the empty cuvette into the cuvette guide and start the air measurement.
            SingleMeasurement air = device.Measure();
            // Dispense the liquid into the cuvette and start the sample measurement.
            SingleMeasurement sample = device.Measure();
            // Aspirate the liquid back into the tip, leave the cuvette guide, and discard tip plus cuvette.
            samples.Add(new Measurement(air, sample));
        }

        Factors factors = Measurement.CalculateFactors(0.0, 10.0, stdLow, stdHigh);

        foreach ((string name, Measurement measurement) in new[]
        {
            ("std high 1", stdHigh[0]),
            ("std low 1", stdLow[0]),
            ("sample 1", samples[0]),
            ("sample 2", samples[1]),
        })
        {
            storage.AppendWithResults(measurement, measurement.GetResults(factors), name, device.Logging());
        }

        storage.Save("run_data.json");
    }
}
```

This example uses two high standards, two low standards, and two samples for clarity.
The same pattern scales directly to other counts: first collect all `std high` measurements, then all `std low` measurements, then the samples, while keeping the low-level sequence `FirstAirMeasurement()`, `FirstSampleMeasurement()`, and then repeated `Measure()` / `Measure()` pairs.

## 4. Opening a Device

Available devices can be enumerated with [`Device.GetAvailableDevices()`][device-getavailabledevices-api]:

```csharp
var devices = Device.GetAvailableDevices();
```

Then create a device either by serial number or by auto-detection:

```csharp
using var device = new Device();
using var deviceBySerial = new Device("SN0010");
```

Recommendations:

- use `using` so the serial connection is disposed reliably
- surface constructor failures clearly, because they usually indicate connection or discovery problems

## 5. Querying Device Information

Basic device metadata can be queried directly:

```csharp
using var device = new Device();

string serialNumber = device.SerialNumber();
string firmwareVersion = device.FirmwareVersion();
string productionNumber = device.ProductionNumber();
```

The library version can be queried separately with [`device.LibraryVersion`][device-libraryversion-api]:

```csharp
string libraryVersion = device.LibraryVersion;
```

## 6. Running a Self-Test

Run the self-test with [`device.SelfTest()`][device-selftest-api]:

```csharp
SelfTestResult result = device.SelfTest();
```

The returned [`SelfTestResult`][selftestresult-api] object provides:

- [`result.Result`][selftestresult-result-api]
- [`result.HasProblems()`][selftestresult-hasproblems-api]
- helper methods such as [`HasProblemWithCommunication()`][selftestresult-hasproblemwithcommunication-api]

## 7. Acquiring Raw Measurements

The explicit low-level workflow for `evifluor` is typically:

1. [`FirstAirMeasurement()`][device-firstairmeasurement-api]
2. [`FirstSampleMeasurement()`][device-firstsamplemeasurement-api]
3. repeated [`Measure()`][device-measure-api] calls for follow-up air and sample acquisitions

Example:

```csharp
FirstAirMeasurementResult air = device.FirstAirMeasurement();
FirstSampleMeasurementResult sample = device.FirstSampleMeasurement();
```

You can check the cuvette holder state before starting with [`device.IsCuvetteHolderEmpty()`][device-iscuvetteholderempty-api]:

```csharp
bool empty = device.IsCuvetteHolderEmpty();
```

## 8. Building a `Measurement`

Create a higher-level [`Measurement`][measurement-api] object from the acquisitions:

```csharp
var measurement = new Measurement(air, sample, "sample A");
```

Or from explicit air and sample measurements:

```csharp
SingleMeasurement airMeasurement = device.Measure();
SingleMeasurement sampleMeasurement = device.Measure();
var measurement = new Measurement(airMeasurement, sampleMeasurement, "sample B");
```

## 9. Calculating Results

Calculated assay results can be calculated with [`measurement.GetResults(...)`][measurement-results-api]:

```csharp
Factors factors = Measurement.CalculateFactors(0.0, 10.0, stdLowMeasurements, stdHighMeasurements);
Results results = measurement.GetResults(factors);
```

Notes:

- the low-level API keeps factor handling explicit
- in a production workflow, correction factors typically come from standards, not from the current sample
- this is the main difference from [`Run`][run-api], which hides these steps

## 10. Persisting Data

Use [`StorageMeasurement`][storage-measurement-api] for persistence:

```csharp
var storage = new StorageMeasurement();
storage.AddDeviceInfo(device, "manual low-level workflow");
storage.AppendWithResults(measurement, results, "sample A", device.Logging());
storage.Save("run_data.json");
```

CSV export example with [`StorageMeasurement.ExportAsCsv(...)`][storage-measurement-exportascsv-api]:

```csharp
StorageMeasurement.ExportAsCsv("run_data.json");
```

## 11. Error Handling and Cleanup

The C# API uses exceptions for communication and workflow failures.

Handle at least these categories:

- device discovery failures
- serial communication failures
- self-test failures according to [`SelfTestResult`][selftestresult-api]
- invalid file paths during persistence

Always dispose the [`Device`][device-api] instance:

```csharp
using var device = new Device();
```

## 12. Notes About `Run`

The [`Run`][run-api] class is intentionally excluded from this chapter because it abstracts away the individual device operations.

[run-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Run.html
[device-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html
[single-measurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.SingleMeasurement.html
[measurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Measurement.html
[storage-measurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.StorageMeasurement.html
[selftestresult-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.SelfTestResult.html
[device-getavailabledevices-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_GetAvailableDevices
[device-serialnumber-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_SerialNumber
[device-firmwareversion-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_FirmwareVersion
[device-productionnumber-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_ProductionNumber
[device-selftest-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_SelfTest
[device-iscuvetteholderempty-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_IsCuvetteHolderEmpty
[device-baseline-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_Baseline
[device-measure-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_Measure
[device-logging-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_Logging
[device-libraryversion-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_LibraryVersion
[device-firstairmeasurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_FirstAirMeasurement
[device-firstsamplemeasurement-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Device.html#Hse_EviFluor_Device_FirstSampleMeasurement_System_Double_
[selftestresult-result-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.SelfTestResult.html#Hse_EviFluor_SelfTestResult_Result
[selftestresult-hasproblems-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.SelfTestResult.html#Hse_EviFluor_SelfTestResult_HasProblems
[selftestresult-hasproblemwithcommunication-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.SelfTestResult.html#Hse_EviFluor_SelfTestResult_HasProblemWithCommunication
[measurement-results-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.Measurement.html#Hse_EviFluor_Measurement_GetResults_Hse_EviFluor_Factors_Hse_EviFluor_IKit_
[storage-measurement-exportascsv-api]: https://hseag.github.io/evi-test/pre-release/doc/api/csharp/api/Hse.EviFluor.StorageMeasurement.html#Hse_EviFluor_StorageMeasurement_ExportAsCsv_System_String_
