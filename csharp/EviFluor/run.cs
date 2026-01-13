using Hse.EviFluor;
using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics.Metrics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static Hse.EviFluor.Verification;

namespace Hse.EviFluor;

/// <summary>
/// Coordinates a guided measurement run: initial air/sample setup, repeated air+sample pairs,
/// verification, logging, on-the-fly factor calculation, and JSON persistence.
/// </summary>
public class Run
{
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
    public Run(int nrOfStdLow, int nrOfStdHigh, double concentration, string? path = null, string? filename = null, string? device = null)
    {
        Filename = null;
        NrOfStdLow_ = nrOfStdLow;
        NrOfStdHigh_ = nrOfStdHigh;
        Concentration_ = concentration;
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
            Factors_ = Measurement.CalculateFactors(0, Concentration_, Storage_.Measurements().GetRange(NrOfStdLow_, NrOfStdHigh_), Storage_.Measurements().GetRange(0, NrOfStdHigh_));
        }

        if (Factors_ != null)
        {
            for (int i = 0; i < Storage_.Count; i++)
            {
                if (!Storage_[i].HasResults())
                {
                    Storage_[i].ApplyResults(Factors_);
                }
            }
        }
    }

    /// <summary>
    /// Executes the next step in the run’s state machine:
    /// <list type="bullet">
    /// <item>FIRST_AIR: records min/max air and verifies</item>
    /// <item>FIRST_SAMPLE: auto-gains, measures sample, verifies, stores</item>
    /// <item>AIR: measures air and verifies</item>
    /// <item>SAMPLE: measures sample, verifies, stores, and returns to AIR</item>
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
                    if (FirstAirMeasurementResult_ == null)
                    {
                        throw new Exception("FirstAirMeasurementResult cant be null!");
                    }

                    FirstSampleMeasurementResult_ = Device_.FirstSampleMeasurement();
                    Verification_.Check(FirstSampleMeasurementResult_);
                    var measurement = new Measurement(FirstAirMeasurementResult_, FirstSampleMeasurementResult_);
                    Storage_.Append(measurement, comment, Device_.Logging(), Verification_);
                    State_ = State.AIR;
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
                    if (Air_ == null)
                    {
                        throw new Exception("Air cant be null!");
                    }

                    Sample_ = Device_.Measure();
                    Verification_.Check(Sample_);
                    var measurement = new Measurement(Air_, Sample_);
                    Storage_.Append(measurement, comment, Device_.Logging(), Verification_);
                    State_ = State.AIR;
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
    /// Returns whether the instrument’s cuvette holder is empty, as reported by the device.
    /// </summary>
    public bool checkEmpty()
    {
        if (Device_ == null)
        {
            throw new Exception("Device cant be null!");
        }
        return Device_.IsCuvetteHolderEmpty();
    }
}

