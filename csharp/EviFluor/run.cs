using Hse.EviFluor;
using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Hse.EviFluor.Kits;
using static Hse.EviFluor.Verification;

namespace Hse.EviFluor;

/// <summary>
/// Coordinates a guided measurement run: initial air/sample setup, repeated air+sample pairs,
/// verification, logging, on-the-fly factor calculation, and JSON persistence.
/// </summary>
public class Run
{
    private readonly bool NoAir_;

    private enum State
    {
        FIRST_AIR,
        FIRST_SAMPLE,
        AIR,
        SAMPLE
    }

    /// <summary>Number of low-standard replicates to collect before factor calculation.</summary>
    private int NrOfStdLow_ = 1;

    /// <summary>Number of high-standard replicates to collect before factor calculation.</summary>
    private int NrOfStdHigh_ = 1;

    /// <summary>Target concentration for the high standard (unit depends on kit).</summary>
    private double Concentration_ = 0.0;

    /// <summary>Destination filename for the JSON log.</summary>
    public string? Filename { get; }
    private Device? Device_ = null;
    private int Count_ = 0;
    private Verification Verification_ = new Verification();
    private StorageMeasurement Storage_ = new StorageMeasurement();
    private Factors? Factors_ = null;
    private readonly IKit Kit_;
    private readonly double SettlingTime_;
    private readonly string? DeviceIdentifier_;
    private State State_ = State.FIRST_AIR;
    private FirstAirMeasurementResult? FirstAirMeasurementResult_ = null;
    private FirstSampleMeasurementResult? FirstSampleMeasurementResult_ = null;
    private SingleMeasurement? Air_ = null;
    private SingleMeasurement? Sample_ = null;

    /// <summary>
    /// Initializes a new measurement run and opens the device.
    /// </summary>
    /// <param name="nrOfStdLow">Replicates for standard low.</param>
    /// <param name="nrOfStdHigh">Replicates for standard high.</param>
    /// <param name="concentration">Concentration assigned to standard high.</param>
    /// <param name="path">Optional folder for the output JSON file.</param>
    /// <param name="filename">Optional file name; generated if <c>null</c>.</param>
    /// <param name="device">Optional device serial or "SIMULATION" for socket mode.</param>
    /// <param name="noAir">If set to <c>true</c>, the run will skip air measurements.</param>
    /// <param name="kit">Optional kit overriding the default fit model and measurement settings.</param>
    /// <param name="settlingTime">Optional explicit settling time override in seconds.</param>
    public Run(int nrOfStdLow, int nrOfStdHigh, double concentration, string? path = null, string? filename = null, string? device = null, bool noAir = false, IKit? kit = null, double? settlingTime = null)
    {
        Filename = null;
        NoAir_ = noAir;
        NrOfStdLow_ = nrOfStdLow;
        NrOfStdHigh_ = nrOfStdHigh;
        Concentration_ = concentration;
        Kit_ = kit ?? new Default();
        SettlingTime_ = settlingTime ?? Kit_.SettlingTime();
        DeviceIdentifier_ = device;
        if (device == null)
        {
            Device_ = new Device();
        }
        else
        {
            Device_ = new Device(device);
        }
        var now = DateTime.UtcNow.ToString("o");

        if (filename != null)
        {
            Filename = filename;
        }
        else
        {
            Filename = string.Format("evifluor-{0}-{1}.json", Device_.SerialNumber(), DateTime.Now.ToString("yyyy_MM_dd_HH_mm_ss"));
        }

        if (path != null)
        {
            Filename = System.IO.Path.Combine(path, Filename);
        }

        State_ = NoAir_ ? State.FIRST_SAMPLE : State.FIRST_AIR;
    }

    private static JsonNode? FirstAirToJson(FirstAirMeasurementResult? firstAir)
    {
        return firstAir?.ToJson();
    }

    private static FirstAirMeasurementResult? FirstAirFromJson(JsonNode? node)
    {
        if (node == null)
        {
            return null;
        }

        return new FirstAirMeasurementResult(
            SingleMeasurement.FromJson(node[Dict.MIN_MEASUREMENT] ?? throw new InvalidOperationException($"{Dict.MIN_MEASUREMENT} is missing or null")),
            SingleMeasurement.FromJson(node[Dict.MAX_MEASUREMENT] ?? throw new InvalidOperationException($"{Dict.MAX_MEASUREMENT} is missing or null")));
    }

    private static JsonNode? FirstSampleToJson(FirstSampleMeasurementResult? firstSample)
    {
        if (firstSample == null)
        {
            return null;
        }

        JsonObject autoGain = new JsonObject
        {
            ["found"] = firstSample.AutoGainResult.Found,
            ["led_power"] = firstSample.AutoGainResult.LedPower,
        };

        return new JsonObject
        {
            ["autoGainResult"] = autoGain,
            ["measurement"] = firstSample.Measurement.ToJson(),
        };
    }

    private static FirstSampleMeasurementResult? FirstSampleFromJson(JsonNode? node)
    {
        if (node == null)
        {
            return null;
        }

        JsonNode autoGain = node["autoGainResult"] ?? throw new InvalidOperationException("autoGainResult is missing or null");
        return new FirstSampleMeasurementResult(
            new AutoGainResult(
                autoGain["found"]?.GetValue<bool>() ?? throw new InvalidOperationException("found is missing or null"),
                autoGain["led_power"]?.GetValue<int>() ?? throw new InvalidOperationException("led_power is missing or null")),
            SingleMeasurement.FromJson(node["measurement"] ?? throw new InvalidOperationException("measurement is missing or null")));
    }

    private static JsonNode? SingleMeasurementToJson(SingleMeasurement? measurement)
    {
        return measurement?.ToJson();
    }

    private static SingleMeasurement? SingleMeasurementFromJson(JsonNode? node)
    {
        return node == null ? null : SingleMeasurement.FromJson(node);
    }

    /// <summary>
    /// Resolves the JSON state filename for a run.
    /// </summary>
    /// <param name="device">Optional device identifier used when no explicit filename is given.</param>
    /// <param name="filename">Optional explicit state filename.</param>
    /// <returns>Resolved state filename.</returns>
    public static string ResolveStateFilename(string? device = null, string? filename = null)
    {
        if (!string.IsNullOrEmpty(filename))
        {
            return filename;
        }
        if (!string.IsNullOrEmpty(device))
        {
            return $"evifluor-{device}-state.json";
        }
        return "state.json";
    }

    /// <summary>
    /// Finalizer that disposes the underlying device if still open.
    /// </summary>
    ~Run()
    {
        if (Device_ != null)
        {
            Device_.Dispose();
        }
    }

    /// <summary>
    /// Computes calibration factors when enough standards are present and applies pending results
    /// to all stored measurements that do not yet have results.
    /// </summary>
    protected void reCalculate()
    {
        if (Factors_ == null && Storage_.Count == NrOfStdLow_ + NrOfStdHigh_)
        {
            Factors_ = Measurement.CalculateFactors(
                0,
                Concentration_,
                Storage_.Measurements().GetRange(NrOfStdLow_, NrOfStdHigh_),
                Storage_.Measurements().GetRange(0, NrOfStdHigh_),
                NoAir_ ? Algorithm.V2 : Algorithm.V1
            );
        }

        if (Factors_ != null)
        {
            for (int i = 0; i < Storage_.Count; i++)
            {
                if (!Storage_[i].HasResults())
                {
                    Storage_[i].ApplyResults(Factors_, Kit_);
                }
            }
        }
    }

    /// <summary>
    /// Executes the next step in the runâ€™s state machine:
    /// <list type="bullet">
    /// <item>FIRST_AIR: records min/max air and verifies</item>
    /// <item>FIRST_SAMPLE: auto-gains, measures sample, verifies, stores</item>
    /// <item>AIR: measures air and verifies</item>
    /// <item>SAMPLE: measures sample, verifies, stores, and returns to AIR or SAMPLE depending on <c>noAir</c></item>
    /// </list>
    /// Saves the updated JSON after each step.
    /// </summary>
    /// <param name="comment">Optional annotation stored with the measurement.</param>
    /// <exception cref="InvalidOperationException">When required intermediate values are missing for the current state.</exception>
    public void measure(string comment = "")
    {
        if (Device_ == null)
        {
            throw new Exception("Device cant be null!");
        }

        switch (State_)
        {
            case State.FIRST_AIR:
                {
                    Verification_ = new Verification();
                    FirstAirMeasurementResult_ = Device_.FirstAirMeasurement();
                    Verification_.Check(FirstAirMeasurementResult_);
                    State_ = State.FIRST_SAMPLE;
                }
                break;

            case State.FIRST_SAMPLE:
                {
                    if (!NoAir_ && FirstAirMeasurementResult_ == null)
                    {
                        throw new Exception("FirstAirMeasurementResult cant be null!");
                    }

                    if (SettlingTime_ > 0.0)
                    {
                        Thread.Sleep((int)(SettlingTime_ * 1000.0));
                    }

                    if (Kit_.StdHighTargetSignalFactor() is double factor)
                    {
                        FirstSampleMeasurementResult_ = Device_.FirstSampleMeasurement(factor);
                    }
                    else
                    {
                        FirstSampleMeasurementResult_ = Device_.FirstSampleMeasurement();
                    }
                    Verification_.Check(
                        FirstSampleMeasurementResult_,
                        stdHighTargetSignalFactor: Kit_.StdHighTargetSignalFactor()
                            ?? Verification.DefaultStdHighTargetSignalFactor);
                    Measurement measurement;

                    if (NoAir_)
                    {
                        measurement = new Measurement(null, FirstSampleMeasurementResult_.Measurement);
                        State_ = State.SAMPLE;
                    }
                    else
                    {
                        measurement = new Measurement(FirstAirMeasurementResult_!, FirstSampleMeasurementResult_);
                        State_ = State.AIR;
                    }

                    Storage_.Append(measurement, comment, Device_.Logging(), Verification_);
                }
                break;

            case State.AIR:
                {
                    Verification_ = new Verification();
                    Air_ = Device_.Measure();
                    Verification_.Check(Air_);
                    State_ = State.SAMPLE;
                }
                break;

            case State.SAMPLE:
                {
                    if (!NoAir_ && Air_ == null)
                    {
                        throw new Exception("Air cant be null!");
                    }

                    if (SettlingTime_ > 0.0)
                    {
                        Thread.Sleep((int)(SettlingTime_ * 1000.0));
                    }

                    Sample_ = Device_.Measure();
                    Verification_.Check(Sample_);
                    var measurement = new Measurement(NoAir_ ? null : Air_, Sample_);
                    Storage_.Append(measurement, comment, Device_.Logging(), Verification_);
                    State_ = NoAir_ ? State.SAMPLE : State.AIR;
                }
                break;
        }
        reCalculate();
        if (Filename == null)
        {
            throw new Exception("Filename cant be null!");
        }
        Storage_.Save(Filename);
        Count_++;
    }

    /// <summary>
    /// Returns whether the instrumentâ€™s cuvette holder is empty, as reported by the device.
    /// </summary>
    public bool checkEmpty()
    {
        if (Device_ == null)
        {
            throw new Exception("Device cant be null!");
        }
        return Device_.IsCuvetteHolderEmpty();
    }

    /// <summary>
    /// Exports the stored measurements as CSV next to the JSON file.
    /// </summary>
    public void exportAsCsv()
    {
        if (Filename == null)
        {
            throw new Exception("Filename cant be null!");
        }
        Storage_.ExportAsCsv(Filename);
    }

    /// <summary>
    /// Persists the current run state to a JSON file.
    /// </summary>
    /// <param name="filename">Optional explicit state filename overriding the default naming.</param>
    public void SaveState(string? filename = null)
    {
        string stateFilename = ResolveStateFilename(DeviceIdentifier_ ?? (Device_ != null && DeviceIdentifier_ != "SIMULATION" ? Device_.SerialNumber() : null), filename);

        if (Filename == null)
        {
            throw new Exception("Filename cant be null!");
        }

        if (Kit_ is not Default defaultKit)
        {
            throw new InvalidOperationException("Only Default-based kits can be saved");
        }

        string deviceValue = DeviceIdentifier_ ?? (Device_ == null ? "SIMULATION" : Device_.SerialNumber());

        JsonObject state = new JsonObject
        {
            ["filename"] = Filename,
            ["nr_of_std_low"] = NrOfStdLow_,
            ["nr_of_std_high"] = NrOfStdHigh_,
            ["concentration"] = Concentration_,
            ["kit"] = defaultKit.ToJson(),
            ["settling_time"] = SettlingTime_,
            ["no_air"] = NoAir_,
            ["count"] = Count_,
            ["state"] = (int)State_,
            ["device"] = deviceValue,
            ["first_air"] = FirstAirToJson(FirstAirMeasurementResult_),
            ["first_sample"] = FirstSampleToJson(FirstSampleMeasurementResult_),
            ["air"] = SingleMeasurementToJson(Air_),
            ["sample"] = SingleMeasurementToJson(Sample_),
            ["factors"] = Factors_?.ToJson(),
        };

        File.WriteAllText(stateFilename, state.ToJsonString());
        Storage_.Save(Filename);
    }

    /// <summary>
    /// Restores a run from a JSON state file previously written by <see cref="SaveState"/>.
    /// </summary>
    /// <param name="filename">Optional explicit state filename overriding the default naming.</param>
    /// <returns>Reconstructed run with restored in-memory state and persisted measurements.</returns>
    public static Run LoadState(string? filename = null)
    {
        string stateFilename = ResolveStateFilename(filename: filename);
        JsonNode state = JsonNode.Parse(File.ReadAllText(stateFilename)) ?? throw new InvalidOperationException("State JSON could not be parsed");

        var run = new Run(
            state["nr_of_std_low"]?.GetValue<int>() ?? throw new InvalidOperationException("nr_of_std_low is missing or null"),
            state["nr_of_std_high"]?.GetValue<int>() ?? throw new InvalidOperationException("nr_of_std_high is missing or null"),
            state["concentration"]?.GetValue<double>() ?? throw new InvalidOperationException("concentration is missing or null"),
            filename: state["filename"]?.GetValue<string>(),
            device: state["device"]?.GetValue<string>(),
            noAir: state["no_air"]?.GetValue<bool>() ?? false,
            kit: state["kit"] is null ? new Default() : Default.FromJson(state["kit"]!),
            settlingTime: state["settling_time"]?.GetValue<double>());

        run.Count_ = state["count"]?.GetValue<int>() ?? throw new InvalidOperationException("count is missing or null");
        run.State_ = (State)(state["state"]?.GetValue<int>() ?? throw new InvalidOperationException("state is missing or null"));
        if (state["factors"] != null)
        {
            run.Factors_ = Factors.FromJson(state["factors"]);
        }
        run.FirstAirMeasurementResult_ = FirstAirFromJson(state["first_air"]);
        run.FirstSampleMeasurementResult_ = FirstSampleFromJson(state["first_sample"]);
        run.Air_ = SingleMeasurementFromJson(state["air"]);
        run.Sample_ = SingleMeasurementFromJson(state["sample"]);

        if (!string.IsNullOrEmpty(run.Filename) && File.Exists(run.Filename))
        {
            run.Storage_ = new StorageMeasurement(run.Filename);
        }
        else
        {
            run.Storage_ = new StorageMeasurement();
        }

        return run;
    }
}

