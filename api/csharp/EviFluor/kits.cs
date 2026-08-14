// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Globalization;
using System.Text.Json.Nodes;
using Hse.EviFluor;

namespace Hse.EviFluor.Kits;

/// <summary>
/// Selects the mathematical model used to convert the interpolated signal into a concentration.
/// </summary>
public enum FitAlgorithm
{
    /// <summary>
    /// Uses a linear function <c>k1 * x + k2</c>.
    /// </summary>
    Linear = 1,

    /// <summary>
    /// Uses a lookup-table interpolation on the normalized signal.
    /// </summary>
    LookupTable = 2,
}

/// <summary>
/// Generic configurable kit implementation used directly or as base class for predefined kits.
/// </summary>
/// <remarks>
/// Initializes a kit with explicit fit parameters and optional measurement behavior.
/// </remarks>
/// <param name="fitAlgorithm">Fit model used to convert the calibrated signal into a concentration.</param>
/// <param name="k1">Primary scale factor applied to the fitted concentration.</param>
/// <param name="k2">Offset added to the fitted concentration after scaling.</param>
/// <param name="k3">Reserved third fit parameter for compatibility with existing kit definitions.</param>
/// <param name="lookupTable">Lookup table used when <paramref name="fitAlgorithm"/> is <see cref="FitAlgorithm.LookupTable"/>.</param>
/// <param name="settlingTime">Recommended settling time in seconds before taking a measurement.</param>
/// <param name="stdHighTargetSignalFactor">Optional target factor for the high standard signal during first-sample auto-gain.</param>
/// <param name="description">Human-readable description used for diagnostics and serialization.</param>
public class Default(
    FitAlgorithm fitAlgorithm = FitAlgorithm.Linear,
    double k1 = 1.0,
    double k2 = 0.0,
    double k3 = 0.0,
    LookupTable? lookupTable = null,
    double settlingTime = 0.0,
    double? stdHighTargetSignalFactor = null,
    string? description = null) : IKit
{
    private const string KitFitAlgorithm = "fitAlgorithm";
    private const string KitK1 = "k1";
    private const string KitK2 = "k2";
    private const string KitK3 = "k3";
    private const string KitLookupTable = "lookupTable";
    private const string KitSettlingTime = "settlingTime";
    private const string KitStdHighTargetSignalFactor = "stdHighTargetSignalFactor";
    private const string KitDescription = "description";

    private readonly FitAlgorithm FitAlgorithm_ = fitAlgorithm;
    private readonly double K1_ = k1;
    private readonly double K2_ = k2;
    private readonly double K3_ = k3;
    private readonly LookupTable? LookupTable_ = lookupTable;
    private readonly double SettlingTime_ = settlingTime;
    private readonly double? StdHighTargetSignalFactor_ = stdHighTargetSignalFactor;
    private readonly string Description_ = description ?? "Default kit with linear fit";

    /// <summary>
    /// Returns a diagnostic string containing the kit description and parameters.
    /// </summary>
    public override string ToString()
    {
        if (FitAlgorithm_ == FitAlgorithm.LookupTable)
        {
            string lookupTableString = LookupTable_ == null ? "None" : "present";
            return $"{Description_} fit_algorithm={FitAlgorithm_}, lookup_table={lookupTableString}, settling_time={FormatNumber(SettlingTime_)}, std_high_target_signal_factor={FormatNullableNumber(StdHighTargetSignalFactor_)}";
        }

        return $"{Description_} fit_algorithm={FitAlgorithm_}, k1={FormatNumber(K1_)}, k2={FormatNumber(K2_)}, k3={FormatNumber(K3_)}, settling_time={FormatNumber(SettlingTime_)}, std_high_target_signal_factor={FormatNullableNumber(StdHighTargetSignalFactor_)}";
    }

    /// <summary>
    /// Serializes the kit configuration to JSON.
    /// </summary>
    public JsonNode ToJson()
    {
        JsonObject obj = new()
        {
            [KitFitAlgorithm] = JsonValue.Create((int)FitAlgorithm_),
            [KitK1] = JsonValue.Create(K1_),
            [KitK2] = JsonValue.Create(K2_),
            [KitK3] = JsonValue.Create(K3_),
            [KitLookupTable] = LookupTable_?.ToJson(),
            [KitSettlingTime] = JsonValue.Create(SettlingTime_),
            [KitDescription] = JsonValue.Create(Description_),
        };

        obj[KitStdHighTargetSignalFactor] = StdHighTargetSignalFactor_ is null
            ? null
            : JsonValue.Create(StdHighTargetSignalFactor_.Value);
        return obj;
    }

    /// <summary>
    /// Deserializes a configurable kit from JSON created by <see cref="ToJson"/>.
    /// </summary>
    /// <param name="node">JSON object containing a serialized kit configuration.</param>
    /// <returns>The deserialized configurable kit instance.</returns>
    public static Default FromJson(JsonNode node)
    {
        JsonObject obj = node as JsonObject ?? throw new InvalidOperationException("Kit JSON must be an object");
        int fitAlgorithmValue = obj[KitFitAlgorithm]?.GetValue<int>()
            ?? throw new InvalidOperationException($"{KitFitAlgorithm} is missing or null");

        if (!Enum.IsDefined(typeof(FitAlgorithm), fitAlgorithmValue))
        {
            throw new InvalidOperationException($"Unknown fit algorithm: {fitAlgorithmValue}");
        }

        return new Default(
            fitAlgorithm: (FitAlgorithm)fitAlgorithmValue,
            k1: obj[KitK1]?.GetValue<double>() ?? 1.0,
            k2: obj[KitK2]?.GetValue<double>() ?? 0.0,
            k3: obj[KitK3]?.GetValue<double>() ?? 0.0,
            lookupTable: obj[KitLookupTable] is null ? null : LookupTable.FromJson(obj[KitLookupTable]!),
            settlingTime: obj[KitSettlingTime]?.GetValue<double>() ?? 0.0,
            stdHighTargetSignalFactor: obj[KitStdHighTargetSignalFactor]?.GetValue<double>(),
            description: obj[KitDescription]?.GetValue<string>());
    }

    /// <summary>
    /// Creates a predefined kit instance from a string name.
    /// </summary>
    /// <param name="name">Preset kit name or alias.</param>
    /// <param name="k1">Optional override for the primary scale factor.</param>
    /// <param name="k2">Optional override for the additive concentration offset.</param>
    /// <param name="k3">Optional override for the reserved third fit parameter.</param>
    /// <param name="lookupTable">Optional lookup table override for presets that support table-based fitting.</param>
    /// <returns>The matching predefined or default kit instance.</returns>
    public static Default Factory(string name, double? k1 = null, double? k2 = null, double? k3 = null, LookupTable? lookupTable = null)
    {
        string normalized = name.ToLowerInvariant();

        if (normalized == "default")
        {
            return new Default(
                k1: k1 ?? 1.0,
                k2: k2 ?? 0.0,
                k3: k3 ?? 0.0,
                lookupTable: lookupTable);
        }
        if (normalized == "qubittm_1x_dsdna_broad_range_br" || normalized == "qubit_br")
        {
            return new QubitTM_1X_dsDNA_Broad_Range_BR(
                k1: k1 ?? 1.0,
                k2: k2 ?? 0.0,
                lookupTable: lookupTable);
        }
        if (normalized == "qubittm_1x_dsdna_high_sensitivity_hs" || normalized == "qubit_hs")
        {
            return new QubitTM_1X_dsDNA_High_Sensitivity_HS(
                k1: k1 ?? 1.0,
                k2: k2 ?? 0.0);
        }

        throw new ArgumentException($"Unknown kit: {name}", nameof(name));
    }

    /// <summary>
    /// Calculates the concentration for a measured signal value using the configured fit model.
    /// </summary>
    /// <param name="stdLow">Low calibration standard used as the lower interpolation anchor.</param>
    /// <param name="stdHigh">High calibration standard used as the upper interpolation anchor.</param>
    /// <param name="value">Measured signal value to convert into a concentration.</param>
    /// <returns>The calculated concentration for the measured signal.</returns>
    public double fit(Point stdLow, Point stdHigh, double value)
    {
        double deltaSignal = stdHigh.Value - stdLow.Value;
        if (deltaSignal == 0)
        {
            throw new InvalidOperationException("Standard low and high must have different signal values for calibration");
        }

        double m = (stdHigh.Concentration - stdLow.Concentration) / deltaSignal;
        double b = stdHigh.Concentration - m * stdHigh.Value;
        double x = m * value + b;

        return FitAlgorithm_ switch
        {
            FitAlgorithm.Linear => x * K1_ + K2_,
            FitAlgorithm.LookupTable => FitLookupTable(stdLow, deltaSignal, value),
            _ => throw new InvalidOperationException($"Unknown fit algorithm: {FitAlgorithm_}"),
        };
    }

    /// <summary>
    /// Returns the default settling time for the kit in seconds.
    /// </summary>
    public double SettlingTime()
    {
        return SettlingTime_;
    }

    /// <summary>
    /// Returns the optional target signal factor used during first-sample auto-gain.
    /// </summary>
    public double? StdHighTargetSignalFactor()
    {
        return StdHighTargetSignalFactor_;
    }

    private double FitLookupTable(Point stdLow, double deltaSignal, double rfu)
    {
        if (LookupTable_ == null || LookupTable_.Entries.Count == 0)
        {
            throw new InvalidOperationException("Lookup table fit algorithm requires a non-empty lookup table");
        }

        if (LookupTable_.Entries.Count == 1)
        {
            return LookupTable_.Entries[0].Concentration;
        }

        double rfuNorm = (rfu - stdLow.Value) / deltaSignal;
        LookupTableEntry lower = LookupTable_.Entries[0];
        LookupTableEntry upper = LookupTable_.Entries[1];

        for (int i = 0; i < LookupTable_.Entries.Count - 1; i++)
        {
            lower = LookupTable_.Entries[i];
            upper = LookupTable_.Entries[i + 1];
            if (rfuNorm <= upper.Signal)
            {
                break;
            }
        }

        double deltaLookupSignal = upper.Signal - lower.Signal;
        if (deltaLookupSignal == 0)
        {
            throw new InvalidOperationException("Lookup table signal values must be strictly monotonic");
        }

        double fraction = (rfuNorm - lower.Signal) / deltaLookupSignal;
        double interpolatedConcentration = lower.Concentration + fraction * (upper.Concentration - lower.Concentration);
        return interpolatedConcentration * K1_ + K2_;
    }

    private static string FormatNullableNumber(double? value)
    {
        return value.HasValue ? FormatNumber(value.Value) : "None";
    }

    private static string FormatNumber(double value)
    {
        string formatted = value.ToString("R", CultureInfo.InvariantCulture);
        if (!formatted.Contains('.') && !formatted.Contains('E') && !formatted.Contains('e'))
        {
            formatted += ".0";
        }
        return formatted;
    }
}

/// <summary>
/// Predefined kit for the Qubit 1X dsDNA high-sensitivity assay.
/// </summary>
/// <remarks>
/// Initializes the Qubit 1X dsDNA high-sensitivity preset.
/// </remarks>
/// <param name="k1">Optional override for the preset's primary scale factor.</param>
/// <param name="k2">Optional override for the preset's additive concentration offset.</param>
public class QubitTM_1X_dsDNA_High_Sensitivity_HS(double k1 = 1.0, double k2 = 0.0) : Default(
        fitAlgorithm: FitAlgorithm.Linear,
        k1: k1,
        k2: k2,
        description: "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit",
        settlingTime: 0.0)
{
}

/// <summary>
/// Predefined kit for the Qubit 1X dsDNA broad-range assay.
/// </summary>
/// <remarks>
/// Initializes the Qubit 1X dsDNA broad-range preset.
/// </remarks>
/// <param name="k1">Optional override for the preset's primary scale factor.</param>
/// <param name="k2">Optional override for the preset's additive concentration offset.</param>
/// <param name="lookupTable">Optional replacement for the preset lookup table.</param>
public class QubitTM_1X_dsDNA_Broad_Range_BR(double k1 = 1.0, double k2 = 0.0, LookupTable? lookupTable = null) : Default(
        fitAlgorithm: FitAlgorithm.LookupTable,
        k1: k1,
        k2: k2,
        lookupTable: lookupTable ?? DefaultLookupTable_,
        description: "QubitTM 1X dsDNA Broad Range (BR) Assay Kit",
        stdHighTargetSignalFactor: 0.4,
        settlingTime: 0.0)
{
    private static readonly LookupTable DefaultLookupTable_ = new(
    [
        new LookupTableEntry(0.0, 8.21960772015573e-19),
        new LookupTableEntry(0.655, 0.005511528146509457),
        new LookupTableEntry(1.15, 0.012096556749881238),
        new LookupTableEntry(10.3, 0.11696146388117148),
        new LookupTableEntry(42.9, 0.4437930749162957),
        new LookupTableEntry(80.5, 0.8584075257182888),
        new LookupTableEntry(100.0, 1.0),
        new LookupTableEntry(101.0, 1.029219428556792),
        new LookupTableEntry(166.0, 1.4952711926922733),
        new LookupTableEntry(242.0, 1.9368286353950304),
    ]);
}
