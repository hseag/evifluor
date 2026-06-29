// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
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
    /// Uses a power-law function <c>k1 * x^k2</c>.
    /// </summary>
    Power = 2,
    /// <summary>
    /// Uses a quadratic function <c>k1 * x^2 + k2 * x + k3</c>.
    /// </summary>
    Quadratic = 3,
}

/// <summary>
/// Generic configurable kit implementation used directly or as base class for predefined kits.
/// </summary>
public class Default : IKit
{
    private const string KitFitAlgorithm = "fitAlgorithm";
    private const string KitK1 = "k1";
    private const string KitK2 = "k2";
    private const string KitK3 = "k3";
    private const string KitSettlingTime = "settlingTime";
    private const string KitStdHighTargetSignalFactor = "stdHighTargetSignalFactor";
    private const string KitDescription = "description";

    private readonly FitAlgorithm FitAlgorithm_;
    private readonly double K1_;
    private readonly double K2_;
    private readonly double K3_;
    private readonly double SettlingTime_;
    private readonly double? StdHighTargetSignalFactor_;
    private readonly string Description_;

    /// <summary>
    /// Initializes a kit with explicit fit parameters and optional measurement behavior.
    /// </summary>
    /// <param name="fitAlgorithm">Fit algorithm applied after the standard-based interpolation step.</param>
    /// <param name="k1">Primary fit parameter.</param>
    /// <param name="k2">Secondary fit parameter.</param>
    /// <param name="k3">Third fit parameter used by the quadratic model.</param>
    /// <param name="settlingTime">Delay in seconds before a sample measurement is acquired.</param>
    /// <param name="stdHighTargetSignalFactor">Optional target factor used during first-sample auto-gain.</param>
    /// <param name="description">Human-readable kit description.</param>
    public Default(
        FitAlgorithm fitAlgorithm = FitAlgorithm.Linear,
        double k1 = 1.0,
        double k2 = 0.0,
        double k3 = 0.0,
        double settlingTime = 0.0,
        double? stdHighTargetSignalFactor = null,
        string? description = null)
    {
        FitAlgorithm_ = fitAlgorithm;
        K1_ = k1;
        K2_ = k2;
        K3_ = k3;
        SettlingTime_ = settlingTime;
        StdHighTargetSignalFactor_ = stdHighTargetSignalFactor;
        Description_ = description ?? "Default kit with linear fit";
    }

    /// <summary>
    /// Returns a diagnostic string containing the kit description and parameters.
    /// </summary>
    /// <returns>Text representation of the configured kit.</returns>
    public override string ToString()
    {
        return $"{Description_} fit_algorithm={FitAlgorithm_}, k1={K1_}, k2={K2_}, k3={K3_}, settling_time={SettlingTime_}, std_high_target_signal_factor={StdHighTargetSignalFactor_}";
    }

    /// <summary>
    /// Serializes the kit configuration to JSON.
    /// </summary>
    /// <returns>JSON node containing the configurable kit fields.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject
        {
            [KitFitAlgorithm] = JsonValue.Create((int)FitAlgorithm_),
            [KitK1] = JsonValue.Create(K1_),
            [KitK2] = JsonValue.Create(K2_),
            [KitK3] = JsonValue.Create(K3_),
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
    /// <param name="node">JSON node containing the kit fields.</param>
    /// <returns>Deserialized <see cref="Default"/> instance.</returns>
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
            k1: obj[KitK1]?.GetValue<double>() ?? throw new InvalidOperationException($"{KitK1} is missing or null"),
            k2: obj[KitK2]?.GetValue<double>() ?? throw new InvalidOperationException($"{KitK2} is missing or null"),
            k3: obj[KitK3]?.GetValue<double>() ?? 0.0,
            settlingTime: obj[KitSettlingTime]?.GetValue<double>() ?? 0.0,
            stdHighTargetSignalFactor: obj[KitStdHighTargetSignalFactor]?.GetValue<double>(),
            description: obj[KitDescription]?.GetValue<string>());
    }

    /// <summary>
    /// Creates a predefined kit instance from a string name.
    /// </summary>
    /// <param name="name">Case-insensitive kit name.</param>
    /// <returns>Matching predefined kit instance.</returns>
    /// <exception cref="ArgumentException">Thrown when the name does not match a known kit.</exception>
    public static Default Factory(string name)
    {
        string normalized = name.ToLowerInvariant();

        if (normalized == "default")
        {
            return new Default();
        }
        if (normalized == "qubittm_1x_dsdna_broad_range_br" || normalized == "qubit_br")
        {
            return new QubitTM_1X_dsDNA_Broad_Range_BR();
        }
        if (normalized == "qubittm_1x_dsdna_high_sensitivity_hs" || normalized == "qubit_hs")
        {
            return new QubitTM_1X_dsDNA_High_Sensitivity_HS();
        }

        throw new ArgumentException($"Unknown kit: {name}", nameof(name));
    }

    /// <summary>
    /// Calculates the concentration for a measured signal value using the configured fit model.
    /// </summary>
    /// <param name="stdLow">Measured low standard.</param>
    /// <param name="stdHigh">Measured high standard.</param>
    /// <param name="value">Measured sample signal.</param>
    /// <returns>Calculated concentration.</returns>
    public double fit(Point stdLow, Point stdHigh, double value)
    {
        double deltaSignal = stdHigh.Value - stdLow.Value;
        if (deltaSignal == 0)
        {
            throw new InvalidOperationException("Standard low and high must have different signal values for calibration");
        }

        var m = (stdHigh.Concentration - stdLow.Concentration) / deltaSignal;
        var b = stdHigh.Concentration - m * stdHigh.Value;
        var x = m * value + b;

        return FitAlgorithm_ switch
        {
            FitAlgorithm.Linear => K1_ * x + K2_,
            FitAlgorithm.Power => x < 0 ? 0.0 : K1_ * Math.Pow(x, K2_),
            FitAlgorithm.Quadratic => x < 0 ? 0.0 : K1_ * Math.Pow(x, 2) + K2_ * x + K3_,
            _ => throw new InvalidOperationException($"Unknown fit algorithm: {FitAlgorithm_}"),
        };
    }

    /// <summary>
    /// Returns the default settling time for the kit in seconds.
    /// </summary>
    /// <returns>Configured settling time in seconds.</returns>
    public double SettlingTime()
    {
        return SettlingTime_;
    }

    /// <summary>
    /// Returns the optional target signal factor used during first-sample auto-gain.
    /// </summary>
    /// <returns>Configured factor, or <c>null</c> when no override is defined.</returns>
    public double? StdHighTargetSignalFactor()
    {
        return StdHighTargetSignalFactor_;
    }
}

/// <summary>
/// Predefined kit for the Qubit 1X dsDNA high-sensitivity assay.
/// </summary>
public class QubitTM_1X_dsDNA_High_Sensitivity_HS : Default
{
    /// <summary>
    /// Initializes the Qubit 1X dsDNA high-sensitivity preset.
    /// </summary>
    public QubitTM_1X_dsDNA_High_Sensitivity_HS()
        : base(
            fitAlgorithm: FitAlgorithm.Linear,
            k1: 1.0,
            k2: 0.0,
            description: "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit",
            settlingTime: 0.0)
    {
    }
}

/// <summary>
/// Predefined kit for the Qubit 1X dsDNA broad-range assay.
/// </summary>
public class QubitTM_1X_dsDNA_Broad_Range_BR : Default
{
    /// <summary>
    /// Initializes the Qubit 1X dsDNA broad-range preset.
    /// </summary>
    public QubitTM_1X_dsDNA_Broad_Range_BR()
        : base(
            fitAlgorithm: FitAlgorithm.Power,
            k1: 1.011658,
            k2: 1.014932,
            description: "QubitTM 1X dsDNA Broad Range (BR) Assay Kit",
            stdHighTargetSignalFactor: 0.4,
            settlingTime: 0.0)
    {
    }
}
