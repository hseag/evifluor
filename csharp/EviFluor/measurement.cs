// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

namespace Hse.EviFluor;

/// <summary>
/// Represents the results the concentration measurement.
/// </summary>
public class Results
{
    /// <summary>
    /// Gets or sets the concentration. The unit of the concentration depends on the used standard high.
    /// </summary>
    public double Concentration { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Results"/> class with specified concentration.
    /// </summary>
    /// <param name="concentration"> The unit of the concentration depends on the used standard high.</param>
    public Results(double concentration)
    {
        Concentration = concentration;
    }

    /// <summary>
    /// Returns a string representation of the results.
    /// </summary>
    /// <returns>A formatted string with the concentration</returns>
    public override string ToString()
    {
        return $"Concentration:{Concentration}";
    }

    /// <summary>
    /// Converts the current instance to a JSON representation.
    /// </summary>
    /// <returns>A <see cref="JsonNode"/> representing the current object.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();

        obj[Dict.CONCENTRATION] = JsonValue.Create(Concentration);

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
            node[Dict.CONCENTRATION]?.GetValue<double>() ?? throw new InvalidOperationException($"{Dict.CONCENTRATION} is missing or null")
        );
    }

    /// <summary>
    /// Determines whether the specified object is equal to the current instance.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the objects are equal; otherwise, <c>false</c>.</returns>
    public override bool Equals(object? obj)
    {
        if (obj is not Results other) return false;

        const double delta = 0.000000001; // Tolerance for floating-point comparisons
        return Math.Abs(Concentration - other.Concentration) < delta;
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(Concentration);
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
    /// Initializes a new instance of the <see cref="Factors"/> class.
    /// </summary>
    /// <param name="stdLow">The low standard factor.</param>
    /// <param name="stdHigh">The high standard factor.</param>
    public Factors(Point stdLow, Point stdHigh)
    {
        StdLow = stdLow;
        StdHigh = stdHigh;
    }

    /// <summary>
    /// Returns a string representation of the standardization factors.
    /// </summary>
    /// <returns>A formatted string displaying the low and high standard factors.</returns>
    public override string ToString()
    {
        return $"StdLow: {StdLow} StdHigh: {StdHigh}";
    }
}


/// <summary>
/// Represents a measurement containing baseline, air, and sample values, along with optional comments.
/// </summary>
public class Measurement
{
    public string comment;
    public SingleMeasurement air;
    public SingleMeasurement sample;

    /// <summary>
    /// Initializes a new instance of the <see cref="Measurement"/> class.
    /// </summary>
    /// <param name="air">The air measurement.</param>
    /// <param name="sample">The sample measurement.</param>
    /// <param name="comment">An optional comment for the measurement.</param>
    public Measurement(SingleMeasurement air, SingleMeasurement sample, string comment = "")
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
    /// Returns a string representation of the measurement.
    /// </summary>
    /// <returns>A formatted string displaying baseline, air, and sample measurements.</returns>
    public override string ToString()
    {
        return $"air:{air} sample:{sample}";
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
    /// Returns the difference between air- and sample measurement.
    /// </summary>
    /// <returns>Difference between air- and sample measurement.</returns>
    public double Value()
    {
        return sample.Delta() - air.Delta();
    }

    /// <summary>
    /// Calculates the concentration.
    /// </summary>
    /// <param name="factors">Factor to calculate the concentration.</param>
    /// <returns></returns>
    public double Concentration(Factors factors)
    {
        var m = (factors.StdHigh.Concentration - factors.StdLow.Concentration) / (factors.StdHigh.Value - factors.StdLow.Value);
        var b = factors.StdHigh.Concentration - m * factors.StdHigh.Value;
        return m * Value() + b;
    }

    /// <summary>
    /// Calculates the results.
    /// </summary>
    /// <param name="factors">Factor to calculate the results.</param>
    /// <returns></returns>
    public Results GetResults(Factors factors)
    {
        return new Results(Concentration(factors));
    }

    /// <summary>
    /// Converts the measurement to a JSON representation.
    /// </summary>
    /// <returns>A JSON node representing the measurement.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();

        obj[Dict.AIR] = air.ToJson();
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
        return new Measurement(            
            SingleMeasurement.FromJson(node[Dict.AIR] ?? throw new InvalidOperationException($"{Dict.AIR} is missing or null")),
            SingleMeasurement.FromJson(node[Dict.SAMPLE] ?? throw new InvalidOperationException($"{Dict.SAMPLE} is missing or null")),
            node.AsObject().ContainsKey(Dict.COMMENT) ? node[Dict.COMMENT]?.ToString() ?? string.Empty : string.Empty
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
    /// <returns>A <see cref="Factors"/> object containing calculated correction factors.</returns>
    public static Factors CalculateFactors(double concentrationLow, double concentrationHigh, List<Measurement> measurementsStdLow, List<Measurement> measurementsStdHigh)
    {
        var countLow = measurementsStdLow.Count;
        var countHigh = measurementsStdHigh.Count;
        double stdLow = 0;
        double stdHigh = 0;

        if (countLow >= 0)
        {
            foreach (Measurement measurement in measurementsStdLow)
            {
                stdLow = stdLow + measurement.Value();
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
                stdHigh = stdHigh + measurement.Value();
            }
            stdHigh = stdHigh / countHigh;
        }
        else
        {
            stdHigh = 1;
        }

        return new Factors(new Point(concentrationLow, stdLow), new Point(concentrationHigh, stdHigh));
    }
}