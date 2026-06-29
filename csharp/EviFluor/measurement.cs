// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Â© 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

namespace Hse.EviFluor;

/// <summary>
/// Measurement algorithms for converting signals to concentrations.
/// </summary>
public enum Algorithm
{
    /// <summary>
    /// Calculates using air and sample values.
    /// </summary>
    V1 = 0,

    /// <summary>
    /// Calculates using sample-only values.
    /// </summary>
    V2 = 1
}

/// <summary>
/// Represents the results the concentration measurement.
/// </summary>
public class Results : IEquatable<Results>, IJsonSerializable
{
    /// <summary>
    /// Gets or sets the concentration. The unit of the concentration depends on the used standard high.
    /// </summary>
    public double Concentration { get; set; }

    /// <summary>
    /// Gets or sets the RFU used as input for concentration calculation.
    /// </summary>
    public double? Rfu { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Results"/> class with specified concentration.
    /// </summary>
    /// <param name="concentration"> The unit of the concentration depends on the used standard high.</param>
    /// <param name="rfu">The RFU used as input for concentration calculation.</param>
    public Results(double concentration, double? rfu = null)
    {
        Concentration = concentration;
        Rfu = rfu;
    }

    /// <summary>
    /// Returns a string representation of the results.
    /// </summary>
    /// <returns>A formatted string with the concentration</returns>
    public override string ToString()
    {
        return $"Concentration:{Concentration} Rfu:{Rfu}";
    }

    /// <summary>
    /// Converts the current instance to a JSON representation.
    /// </summary>
    /// <returns>A <see cref="JsonNode"/> representing the current object.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();

        obj[Dict.CONCENTRATION] = JsonValue.Create(Concentration);
        if (Rfu.HasValue)
        {
            obj[Dict.RFU] = JsonValue.Create(Rfu.Value);
        }

        return obj;
    }

    /// <summary>
    /// Creates a <see cref="Results"/> instance from a JSON representation.
    /// </summary>
    /// <param name="node">The JSON node containing the nucleic acid data.</param>
    /// <returns>A <see cref="Results"/> object populated from the JSON data.</returns>
    /// <exception cref="ArgumentNullException">Thrown if the provided JSON node is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown if required fields are missing or null.</exception>
    public static Results FromJson(JsonNode? node)
    {
        if (node == null) throw new ArgumentNullException(nameof(node));
        return new Results(
            node[Dict.CONCENTRATION]?.GetValue<double>() ?? throw new InvalidOperationException($"{Dict.CONCENTRATION} is missing or null"),
            node[Dict.RFU]?.GetValue<double>()
        );
    }

    /// <summary>
    /// Determines whether the specified object is equal to the current instance.
    /// </summary>
    /// <param name="other">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the objects are equal; otherwise, <c>false</c>.</returns>
    /// <remarks>
    /// Equality uses a relative tolerance of 1e-13 to align with the Python implementation.
    /// </remarks>
    /// 
    public bool Equals(Results? other)
    {
        if (other is null) return false;

        const double delta = 1e-13;
        bool concentrationEqual = Math.Abs(Concentration - other.Concentration) <= delta * Math.Max(Math.Abs(Concentration), Math.Abs(other.Concentration));
        if (!concentrationEqual)
        {
            return false;
        }

        if (!Rfu.HasValue || !other.Rfu.HasValue)
        {
            return true;
        }

        return Math.Abs(Rfu.Value - other.Rfu.Value) <= delta * Math.Max(Math.Abs(Rfu.Value), Math.Abs(other.Rfu.Value));
    }

    /// <summary>
    /// Determines whether the specified object is equal to the current instance.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the objects are equal; otherwise, <c>false</c>.</returns>
    public override bool Equals(object? obj) =>
    Equals(obj as Results);

    /// <summary>
    /// Returns a hash code for the current <see cref="Measurement"/> instance.
    /// </summary>
    /// <returns>
    /// An integer hash code based on the air and sample measurements, as well as the optional comment.
    /// </returns>
    /// <remarks>
    /// This override ensures that instances with the same measurement data produce the same hash code,
    /// which is particularly important when using this class in hash-based collections like dictionaries or hash sets.
    /// </remarks>
    public override int GetHashCode()
    {
        return HashCode.Combine(Concentration, Rfu);
    }
}

/// <summary>
/// Represents a data point with a concentration and corresponding value.
/// </summary>
public class Point
{
    /// <summary>
    /// Gets or sets the concentration value.
    /// </summary>
    public double Concentration { get; set; }

    /// <summary>
    /// Gets or sets the measured value.
    /// </summary>
    public double Value { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Point"/> class with specified concentration and value.
    /// </summary>
    /// <param name="concentration"></param>
    /// <param name="value"></param>
    public Point(double concentration, double value )
    {
        Concentration = concentration;
        Value = value;
    }

    /// <summary>
    /// Returns a string representation of the data point.
    /// </summary>
    /// <returns>A formatted string displaying the concentration and value.</returns>
    public override string ToString()
    {
        return $"Concentration: {Concentration} Value: {Value}";
    }

    /// <summary>
    /// Converts the point to a JSON representation.
    /// </summary>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();
        obj[Dict.CONCENTRATION] = Concentration;
        obj[Dict.VALUE] = Value;
        return obj;
    }

    /// <summary>
    /// Creates a point from a JSON representation.
    /// </summary>
    public static Point FromJson(JsonNode? node)
    {
        if (node == null) throw new ArgumentNullException(nameof(node));
        return new Point(
            node[Dict.CONCENTRATION]?.GetValue<double>() ?? throw new InvalidOperationException($"{Dict.CONCENTRATION} is missing or null"),
            node[Dict.VALUE]?.GetValue<double>() ?? throw new InvalidOperationException($"{Dict.VALUE} is missing or null")
        );
    }
}

/// <summary>
/// Represents standardization factors with low and high values.
/// </summary>
public class Factors
{
    /// <summary>
    /// Gets or sets the low standard factor.
    /// </summary>
    public Point StdLow { get; set; }

    /// <summary>
    /// Gets or sets the high standard factor.
    /// </summary>
    public Point StdHigh { get; set; }

    /// <summary>
    /// Gets or sets the averaged standard-low measurement used as sample-only baseline in algorithm V2.
    /// </summary>
    public double MeasurementStdLow { get; set; }

    /// <summary>
    /// Gets or sets the algorithm used to derive the factors.
    /// </summary>
    public Algorithm? Algorithm { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Factors"/> class.
    /// </summary>
    /// <param name="stdLow">The low standard factor.</param>
    /// <param name="stdHigh">The high standard factor.</param>
    /// <param name="measurementStdLow">The averaged standard-low measurement used as sample-only baseline in algorithm V2.</param>
    /// <param name="algorithm">The algorithm to use for factor calculation.</param>
    public Factors(Point stdLow, Point stdHigh, double measurementStdLow = 0.0, Algorithm? algorithm = null)
    {
        StdLow = stdLow;
        StdHigh = stdHigh;
        MeasurementStdLow = measurementStdLow;
        Algorithm = algorithm;
    }

    /// <summary>
    /// Returns a string representation of the standardization factors.
    /// </summary>
    /// <returns>A formatted string displaying the low and high standard factors.</returns>
    public override string ToString()
    {
        return $"StdLow: {StdLow} StdHigh: {StdHigh} MeasurementStdLow: {MeasurementStdLow} Algorithm: {Algorithm}";
    }

    /// <summary>
    /// Converts the factors to a JSON representation.
    /// </summary>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();
        obj[Dict.STD_LOW] = StdLow.ToJson();
        obj[Dict.STD_HIGH] = StdHigh.ToJson();
        obj[Dict.MEASUREMENT_STD_LOW] = MeasurementStdLow;
        obj[Dict.ALGORITHM] = Algorithm == null ? null : (int)Algorithm;
        return obj;
    }

    /// <summary>
    /// Creates factors from a JSON representation.
    /// </summary>
    public static Factors FromJson(JsonNode? node)
    {
        if (node == null) throw new ArgumentNullException(nameof(node));
        Algorithm? algorithm = null;
        if (node[Dict.ALGORITHM] != null)
        {
            algorithm = (Algorithm)node[Dict.ALGORITHM]!.GetValue<int>();
        }
        return new Factors(
            Point.FromJson(node[Dict.STD_LOW] ?? throw new InvalidOperationException($"{Dict.STD_LOW} is missing or null")),
            Point.FromJson(node[Dict.STD_HIGH] ?? throw new InvalidOperationException($"{Dict.STD_HIGH} is missing or null")),
            node[Dict.MEASUREMENT_STD_LOW]?.GetValue<double>() ?? 0.0,
            algorithm
        );
    }
}


/// <summary>
/// Represents a measurement containing baseline, air, and sample values, along with optional comments.
/// </summary>
public class Measurement : IJsonSerializable
{
    /// <summary>
    /// Optional comment associated with the measurement, such as notes or labels.
    /// </summary>
    public string comment;

    /// <summary>
    /// The air reference measurement used for background correction.
    /// </summary>
    public SingleMeasurement? air;

    /// <summary>
    /// The actual sample measurement.
    /// </summary>
    public SingleMeasurement sample;

    /// <summary>
    /// Initializes a new instance of the <see cref="Measurement"/> class.
    /// </summary>
    /// <param name="air">The air measurement.</param>
    /// <param name="sample">The sample measurement.</param>
    /// <param name="comment">An optional comment for the measurement.</param>
    public Measurement(SingleMeasurement? air, SingleMeasurement sample, string comment = "")
    {
        this.air = air;
        this.sample = sample;
        this.comment = comment;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Measurement"/> class.
    /// </summary>
    /// <param name="air">The air measurement.</param>
    /// <param name="sample">The sample measurement.</param>
    /// <param name="comment">An optional comment for the measurement.</param>
    public Measurement(FirstAirMeasurementResult air, FirstSampleMeasurementResult sample, string comment = "")
    {
        this.air = air.AdjustToLedPower(sample.AutoGainResult.LedPower);
        this.sample = sample.Measurement;
        this.comment = comment;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Measurement"/> class from a first-sample result without air.
    /// </summary>
    public Measurement(FirstSampleMeasurementResult sample, string comment = "")
    {
        this.air = null;
        this.sample = sample.Measurement;
        this.comment = comment;
    }

    /// <summary>
    /// Returns a string representation of the measurement.
    /// </summary>
    /// <returns>A formatted string displaying baseline, air, and sample measurements.</returns>
    public override string ToString()
    {
        if (air == null)
        {
            return $"sample:{sample} comment:{comment}";
        }
        return $"air:{air} sample:{sample} comment:{comment}";
    }

    /// <summary>
    /// Sets the comment for the measurement.
    /// </summary>
    /// <param name="comment">The comment text.</param>
    public void SetComment(string comment)
    {
        this.comment = comment;
    }

    /// <summary>
    /// Gets the comment associated with the measurement.
    /// </summary>
    /// <returns>The comment text.</returns>
    public string Comment()
    {
        return comment;
    }

    /// <summary>
    /// Computes the background-corrected signal by subtracting the air delta from the sample delta.
    /// </summary>
    /// <returns>The corrected signal (same unit as channel mV).</returns>
    public double Value(Algorithm algorithm = Algorithm.V1)
    {
        if (algorithm == Algorithm.V1)
        {
            if (air == null)
            {
                throw new InvalidOperationException("Air measurement is required for Algorithm.V1");
            }
            return sample.Delta() - air.Delta();
        }

        return sample.Delta();
    }

    /// <summary>
    /// Calculates the concentration using the given factors and kit.
    /// </summary>
    /// <param name="factors">Correction factors for the measurement.</param>
    /// <param name="kit">Optional kit for concentration fitting (e.g., linear interpolation).</param>
    /// <returns>The calculated concentration value.</returns>
    public double Concentration(Factors factors, IKit ? kit = null)
    {
        kit = kit ?? new Kits.Default();
        return kit.fit(factors.StdLow, factors.StdHigh, RfuValue(factors));
    }

    /// <summary>
    /// Calculates the RFU used as input for concentration fitting.
    /// </summary>
    /// <param name="factors">Correction factors for the measurement.</param>
    /// <returns>The RFU value.</returns>
    public double RfuValue(Factors factors)
    {
        return Value(factors.Algorithm ?? Algorithm.V1) - factors.MeasurementStdLow;
    }

    /// <summary>
    /// Computes the measurement results using the provided factors and kit.
    /// </summary>
    /// <param name="factors">Factors used for calibration or adjustment.</param>
    /// <param name="kit">Optional kit to use for fitting measured data.</param>
    /// <returns>A <see cref="Results"/> object with computed values.</returns>
    public Results GetResults(Factors factors, IKit ? kit = null)
    {
        return new Results(Concentration(factors, kit), RfuValue(factors));
    }

    /// <summary>
    /// Converts the measurement to a JSON representation.
    /// </summary>
    /// <returns>A JSON node representing the measurement.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();

        if (air != null)
        {
            obj[Dict.AIR] = air.ToJson();
        }
        obj[Dict.SAMPLE] = sample.ToJson();

        if (!String.IsNullOrEmpty(comment))
        {
            obj[Dict.COMMENT] = JsonValue.Create(comment);
        }

        return obj;
    }

    /// <summary>
    /// Creates a <see cref="Measurement"/> instance from a JSON representation.
    /// </summary>
    /// <param name="node">The JSON node containing the measurement data.</param>
    /// <returns>A <see cref="Measurement"/> object populated from JSON data.</returns>
    /// <exception cref="ArgumentNullException">Thrown if the provided JSON node is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown if required fields are missing.</exception>
    public static Measurement FromJson(JsonNode? node)
    {
        if (node == null) throw new ArgumentNullException(nameof(node));
        var obj = node.AsObject();
        return new Measurement(
            obj.ContainsKey(Dict.AIR) && obj[Dict.AIR] is JsonNode airNode && airNode != null
                ? SingleMeasurement.FromJson(airNode)
                : null,
            SingleMeasurement.FromJson(obj[Dict.SAMPLE] ?? throw new InvalidOperationException($"{Dict.SAMPLE} is missing or null")),
            obj.ContainsKey(Dict.COMMENT) ? obj[Dict.COMMENT]?.ToString() ?? string.Empty : string.Empty
        );
    }

    /// <summary>
    /// Calculates the correction factors based on known standard concentrations and corresponding measurements.
    /// </summary>
    /// <param name="concentrationLow">The known low concentration standard.</param>
    /// <param name="concentrationHigh">The known high concentration standard.</param>
    /// <param name="measurementStdLow">The measurement corresponding to the low concentration.</param>
    /// <param name="measurementStdHigh">The measurement corresponding to the high concentration.</param>
    /// <returns>A <see cref="Factors"/> object containing calculated correction factors.</returns>
    /// <remarks>
    /// When multiple measurements are provided, their corrected signals are averaged per level.
    /// Callers must ensure counts &gt; 0; otherwise the average will be undefined.
    /// </remarks>
    public static Factors CalculateFactors(double concentrationLow, double concentrationHigh, Measurement measurementStdLow, Measurement measurementStdHigh)
    {
        List<Measurement> measurementsStdLow = new List<Measurement>() { measurementStdLow  };
        List<Measurement> measurementsStdHigh = new List<Measurement>() { measurementStdHigh };

        return CalculateFactors(concentrationLow, concentrationHigh, measurementsStdLow, measurementsStdHigh);
    }

    /// <summary>
    /// Calculates correction factors using multiple measurements for each concentration level.
    /// </summary>
    /// <param name="concentrationLow">The known low concentration standard.</param>
    /// <param name="concentrationHigh">The known high concentration standard.</param>
    /// <param name="measurementsStdLow">A list of measurements corresponding to the low concentration.</param>
    /// <param name="measurementsStdHigh">A list of measurements corresponding to the high concentration.</param>
    /// <param name="algorithm">The algorithm to use for factor calculation.</param>
    /// <returns>A <see cref="Factors"/> object containing calculated correction factors.</returns>
   
    public static Factors CalculateFactors(double concentrationLow, double concentrationHigh, List<Measurement> measurementsStdLow, List<Measurement> measurementsStdHigh, Algorithm algorithm = Algorithm.V1)
    {
        var countLow = measurementsStdLow.Count;
        var countHigh = measurementsStdHigh.Count;
        double stdLow = 0;
        double stdHigh = 0;

        if (countLow >= 0)
        {
            foreach (Measurement measurement in measurementsStdLow)
            {
                stdLow = stdLow + measurement.Value(algorithm);
            }
            stdLow = stdLow / countLow;
        }
        else
        {
            stdLow = 1;
        }

        if (countHigh >= 0)
        {
            foreach (Measurement measurement in measurementsStdHigh)
            {
                stdHigh = stdHigh + measurement.Value(algorithm);
            }
            stdHigh = stdHigh / countHigh;
        }
        else
        {
            stdHigh = 1;
        }

        if (algorithm == Algorithm.V2)
        {
            return new Factors(
                new Point(concentrationLow, stdLow - stdLow),
                new Point(concentrationHigh, stdHigh - stdLow),
                stdLow,
                algorithm
            );
        }

        return new Factors(new Point(concentrationLow, stdLow), new Point(concentrationHigh, stdHigh), algorithm: algorithm);
    }
}
