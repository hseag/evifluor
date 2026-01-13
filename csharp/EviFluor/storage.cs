// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
namespace Hse.EviFluor;

/// <summary>
/// Represents an entry in the storage measurement system.
/// Contains a measurement, an optional comment, results, and raw JSON data.
/// </summary>
public class StorageMeasurementEntry
{
    /// <summary>
    /// The stored measurement data.
    /// </summary>
    public Measurement Measurement { get; set; }

    /// <summary>
    /// An optional comment associated with the measurement entry.
    /// </summary>
    public String? Comment { get; set; }

    /// <summary>
    /// The calculated results associated with the measurement, if available.
    /// </summary>
    public Results? Results { get; set; }

    /// <summary>
    /// The raw JSON node representation of the measurement entry.
    /// </summary>
    public JsonNode? Node { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="StorageMeasurementEntry"/> class.
    /// </summary>
    /// <param name="measurement">The measurement data.</param>
    /// <param name="comment">An optional comment.</param>
    /// <param name="results">The associated results, if available.</param>
    /// <param name="node">The raw JSON node, if available.</param>
    public StorageMeasurementEntry(Measurement measurement, String? comment = null, Results? results = null, JsonNode? node = null)
    {
        Measurement = measurement;
        Comment = comment;
        Results = results;
        Node = node;
    }

    /// <summary>
    /// Returns a string representation of the storage measurement entry.
    /// </summary>
    /// <returns>A formatted string displaying measurement details.</returns>
    public override string ToString()
    {
        return $"Measurement:{Measurement} Comment:{Comment} Results:{Results}";
    }

    /// <summary>
    /// Determines whether the entry contains calculated results.
    /// </summary>
    /// <returns><c>true</c> if results exist, otherwise <c>false</c>.</returns>
    public bool HasResults()
    {
        return Results != null;
    }

    /// <summary>
    /// Applies the calculated results based on given correction factors.
    /// Updates the JSON node representation if available.
    /// </summary>
    /// <param name="factors">The correction factors to apply.</param>
    /// <remarks>
    /// When the entry was loaded from JSON (<see cref="Node"/> != <c>null</c>), the computed results are
    /// written back into that JSON node under <c>"results"</c>.
    /// </remarks> 
    public void ApplyResults(Factors factors)
    {
        if (Node != null)
        {
            Node[Dict.RESULTS] = Measurement.GetResults(factors).ToJson();
        }
    }

    /// <summary>
    /// Creates a <see cref="StorageMeasurementEntry"/> instance from a JSON node.
    /// Parses the measurement, comment, and results data.
    /// </summary>
    /// <param name="node">The JSON node containing the measurement entry data.</param>
    /// <returns>A populated <see cref="StorageMeasurementEntry"/> instance.</returns>
    public static StorageMeasurementEntry FromJson(JsonNode node)
    {
        Results? results = null;
        String? comment = null;

        if (node.AsObject().ContainsKey(Dict.RESULTS))
        {
            results = Results.FromJson(node[Dict.RESULTS]);
        }

        if (node.AsObject().ContainsKey(Dict.COMMENT))
        {
            if (node is JsonObject jsonObject &&
            jsonObject.TryGetPropertyValue(Dict.COMMENT, out JsonNode? commentNode) &&
            commentNode is not null)
            {
                comment = commentNode.GetValue<string>();
            }
        }
        return new StorageMeasurementEntry(Measurement.FromJson(node), comment, results, node);
    }
}


/// <summary>
/// Handles storage and retrieval of measurements using JSON serialization.
/// </summary>
public class StorageMeasurement
{
    /// <summary>
    /// Raw JSON structure representing all stored measurement data.
    /// This node may contain measurements, results, metadata, logging, and other associated entries.
    /// </summary>
    public JsonNode data { get; }


    /// <summary>
    /// Initializes a new instance of the <see cref="StorageMeasurement"/> class, optionally loading from a file.
    /// </summary>
    /// <param name="filename">Optional filename to load measurements from.</param>
    public StorageMeasurement(string filename = "")
    {
        if (string.IsNullOrEmpty(filename))
        {
            data = new JsonObject();
            data.AsObject()[Dict.MEASUREMENTS] = new JsonArray();
        }
        else
        {
            using (var reader = new StreamReader(filename))
            {
                var json = reader.ReadToEnd();
                data = JsonNode.Parse(json) ?? new JsonObject();
            }
        }
    }

    /// <summary>
    /// Appends a measurement to storage.
    /// </summary>
    /// <param name="measurement">The measurement to append.</param>
    /// <param name="comment">An optional comment for the measurement.</param>
    /// <param name="logging">Optional logging information.</param>
    /// <param name="verification">Optional verification information.</param>
    /// <remarks>
    /// Adds <c>date_time</c> in ISO-8601 UTC and optional <c>logging</c>/<c>errors</c> sections if provided.
    /// </remarks>
    public void Append(Measurement measurement, string comment = "", List<string> ? logging = null, Verification? verification = null)
    {
        if (measurement == null)
            throw new ArgumentException("No measurement object provided to append!");

        var m = measurement.ToJson();
        if (!string.IsNullOrEmpty(comment))
        {
            m[Dict.COMMENT] = comment;
        }

        if (logging != null && logging.Count > 0)
        {
            m[Dict.LOGGING] = new JsonArray();
            foreach( var log in logging)
            {
                m[Dict.LOGGING]?.AsArray().Add(log);
            }
        }

        m[Dict.DATE_TIME] = DateTime.UtcNow.ToString("o");

        if (verification != null && verification.Failed())
        {
            m[Dict.ERRORS] = verification.ToJson();
        }

        data[Dict.MEASUREMENTS]?.AsArray().Add(m);
    }

    /// <summary>
    /// Appends a measurement and the results to storage.
    /// </summary>
    /// <param name="measurement">The measurement to append.</param>
    /// /// <param name="results">The results to append.</param>
    /// <param name="comment">An optional comment for the measurement.</param>
    /// <param name="logging">Optional logging information.</param>
    /// <param name="verification">Optional verification information.</param>
    /// <remarks>
    /// Adds <c>date_time</c> in ISO-8601 UTC and optional <c>logging</c>/<c>errors</c> sections if provided.
    /// </remarks>
    public void AppendWithResults(Measurement measurement, Results results, string comment = "", List<string>? logging = null, Verification ? verification = null)
    {
        if (measurement == null)
            throw new ArgumentException("No measurement object provided to append!");

        var m = measurement.ToJson();

        if (results != null)
            m[Dict.RESULTS] = results.ToJson();

        if (!string.IsNullOrEmpty(comment))
        {
            m[Dict.COMMENT] = comment;
        }

        if (logging != null && logging.Count > 0)
        {
            m[Dict.LOGGING] = new JsonArray();
            foreach (var log in logging)
            {
                m[Dict.LOGGING]?.AsArray().Add(log);
            }
        }

        m[Dict.DATE_TIME] = DateTime.UtcNow.ToString("o");

        if(verification != null && verification.Failed())
        {
            m[Dict.ERRORS] = verification.ToJson();
        }

        data[Dict.MEASUREMENTS]?.AsArray().Add(m);
    }

    /// <summary>
    /// Saves the measurement data to a specified file.
    /// </summary>
    /// <param name="filename">The filename to save data to.</param>
    public void Save(string filename)
    {
        var options = new JsonSerializerOptions
        {
            NumberHandling = JsonNumberHandling.AllowReadingFromString | JsonNumberHandling.AllowNamedFloatingPointLiterals,
            WriteIndented = true,
            TypeInfoResolver = new DefaultJsonTypeInfoResolver()
        };

        using (var writer = new StreamWriter(filename))
        {
            var json = data.ToJsonString(options);
            writer.Write(json);
        }
    }

    /// <summary>
    /// Retrieves the list of stored measurements.
    /// </summary>
    /// <returns>A list of <see cref="Measurement"/> objects.</returns>
    public List<Measurement> Measurements()
    {
        var ret = new List<Measurement>();

        foreach (var m in data[Dict.MEASUREMENTS]?.AsArray() ?? new JsonArray())
            if (m != null)
                ret.Add(Measurement.FromJson(m));

        return ret;
    }

    /// <summary>
    /// Retrieves the list of stored results.
    /// </summary>
    /// <returns>A list of <see cref="Measurement"/> objects.</returns>
    public List<Results> Results()
    {
        var ret = new List<Results>();

        foreach (var m in data[Dict.MEASUREMENTS]?.AsArray() ?? new JsonArray())
        {
            if (m != null && m.AsObject().ContainsKey(Dict.RESULTS) && m[Dict.RESULTS] != null)
                ret.Add(EviFluor.Results.FromJson(m[Dict.RESULTS]));
        }

        return ret;
    }

    /// <summary>
    /// Gets the <see cref="StorageMeasurementEntry"/> at the specified index.
    /// </summary>
    /// <param name="index">The zero-based index of the measurement entry to retrieve.</param>
    /// <returns>
    /// The <see cref="StorageMeasurementEntry"/> located at the given index in the measurement list.
    /// </returns>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if <paramref name="index"/> is outside the range of stored measurements.
    /// </exception>
    public StorageMeasurementEntry this[int index]
    {
        get
        {
            var measurementsArray = data[Dict.MEASUREMENTS]?.AsArray();
            if (measurementsArray == null || index < 0 || index >= measurementsArray.Count)
                throw new IndexOutOfRangeException("CustomRange index out of range");

            var node = measurementsArray.ElementAt(index);

            if(node == null)
                throw new IndexOutOfRangeException("CustomRange index out of range");

            return StorageMeasurementEntry.FromJson(node);
        }
    }

    /// <summary>
    /// Gets the number of stored measurements.
    /// </summary>
    public int Count => data[Dict.MEASUREMENTS]?.AsArray().Count ?? 0;
}