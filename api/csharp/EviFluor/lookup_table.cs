// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;

namespace Hse.EviFluor.Kits;

/// <summary>
/// Single lookup-table point mapping normalized signal to concentration.
/// </summary>
/// <remarks>
/// Initializes a lookup-table entry.
/// </remarks>
public sealed class LookupTableEntry(double concentration, double signal)
{

    /// <summary>
    /// Concentration represented by the lookup-table point.
    /// </summary>
    public double Concentration { get; } = concentration;

    /// <summary>
    /// Normalized signal represented by the lookup-table point.
    /// </summary>
    public double Signal { get; } = signal;

    internal JsonObject ToJsonObject()
    {
        return new JsonObject
        {
            ["concentration"] = Concentration,
            ["signal"] = Signal,
        };
    }

    internal static LookupTableEntry FromJson(JsonNode? node)
    {
        JsonObject obj = node as JsonObject ?? throw new InvalidOperationException("Lookup table entries must be objects");
        return new LookupTableEntry(
            concentration: obj["concentration"]?.GetValue<double>() ?? throw new InvalidOperationException("Lookup table entries must contain concentration"),
            signal: obj["signal"]?.GetValue<double>() ?? throw new InvalidOperationException("Lookup table entries must contain signal"));
    }
}

/// <summary>
/// Stores lookup-table points and converts between CSV and JSON representations.
/// </summary>
/// <remarks>
/// Initializes the lookup table with optional point entries.
/// </remarks>
public sealed class LookupTable(IEnumerable<LookupTableEntry>? entries = null)
{

    /// <summary>
    /// Sorted lookup-table entries. The smallest signal is always at the beginning.
    /// </summary>
    public IReadOnlyList<LookupTableEntry> Entries { get; } = (entries ?? [])
            .OrderBy(entry => entry.Signal)
            .ToList()
            .AsReadOnly();

    /// <summary>
    /// Returns the lookup table as a JSON-serializable array.
    /// </summary>
    public JsonArray ToJson()
    {
        JsonArray array = [];
        foreach (var entry in Entries)
        {
            array.Add(entry.ToJsonObject());
        }
        return array;
    }

    /// <summary>
    /// Writes the lookup table to a JSON file.
    /// </summary>
    public void SaveJson(string jsonPath)
    {
        var parentDirectory = Path.GetDirectoryName(jsonPath);
        if (!string.IsNullOrEmpty(parentDirectory))
        {
            Directory.CreateDirectory(parentDirectory);
        }

        File.WriteAllText(jsonPath, ToJson().ToJsonString(new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
    }

    /// <summary>
    /// Loads a lookup table from a CSV or JSON file based on its extension.
    /// </summary>
    public static LookupTable Load(string path)
    {
        string extension = Path.GetExtension(path).ToLowerInvariant();
        return extension switch
        {
            ".json" => LoadJson(path),
            ".csv" => FromCsv(path),
            _ => throw new InvalidOperationException($"Unsupported lookup table file extension: {(string.IsNullOrEmpty(extension) ? "<none>" : extension)}"),
        };
    }

    /// <summary>
    /// Loads a lookup table from a JSON file.
    /// </summary>
    public static LookupTable LoadJson(string jsonPath)
    {
        JsonNode? node = JsonNode.Parse(File.ReadAllText(jsonPath));
        return node == null ? throw new InvalidOperationException("Lookup table JSON is empty") : FromJson(node);
    }

    /// <summary>
    /// Creates a lookup table from JSON data.
    /// </summary>
    public static LookupTable FromJson(JsonNode node)
    {
        if (node is JsonObject wrapper)
        {
            node = wrapper["lookupTable"] ?? throw new InvalidOperationException("Lookup table JSON must contain lookupTable");
        }

        JsonArray array = node as JsonArray ?? throw new InvalidOperationException("Lookup table JSON must contain a list of entries");
        return new LookupTable(array.Select(LookupTableEntry.FromJson));
    }

    /// <summary>
    /// Builds a lookup table from an RFU CSV file.
    /// </summary>
    public static LookupTable FromCsv(string csvPath)
    {
        string[] lines = File.ReadAllLines(csvPath);
        if (lines.Length == 0)
        {
            throw new InvalidOperationException("CSV file is empty");
        }

        string[] header = lines[0].Split(';');
        int rfuIndex = Array.IndexOf(header, "RFU");
        int concentrationIndex = Array.IndexOf(header, "Concentration");

        if (rfuIndex < 0 || concentrationIndex < 0)
        {
            throw new InvalidOperationException("CSV file is missing columns: RFU, Concentration");
        }

        List<(double Concentration, double Rfu)> rows = [];
        for (int rowIndex = 1; rowIndex < lines.Length; rowIndex++)
        {
            if (string.IsNullOrWhiteSpace(lines[rowIndex]))
            {
                continue;
            }

            string[] row = lines[rowIndex].Split(';');
            string rfuText = GetColumnValue(row, rfuIndex).Trim();
            string concentrationText = GetColumnValue(row, concentrationIndex).Trim();

            if (rfuText.Length == 0 && concentrationText.Length == 0)
            {
                continue;
            }

            if (rfuText.Length == 0 || concentrationText.Length == 0)
            {
                throw new InvalidOperationException($"CSV row {rowIndex + 1} must contain RFU and Concentration");
            }

            rows.Add((
                Concentration: double.Parse(concentrationText, CultureInfo.InvariantCulture),
                Rfu: double.Parse(rfuText, CultureInfo.InvariantCulture)));
        }

        if (rows.Count < 2)
        {
            throw new InvalidOperationException("CSV file must contain at least two data rows to derive RFU normalization");
        }

        double rfuStdHigh = rows[0].Rfu;
        double rfuStdLow = rows[1].Rfu;
        if (rfuStdHigh == rfuStdLow)
        {
            throw new InvalidOperationException("RFU standard high and standard low must be different");
        }

        List<LookupTableEntry> entries = [];
        foreach (var row in rows)
        {
            entries.Add(new LookupTableEntry(
                concentration: row.Concentration,
                signal: (row.Rfu - rfuStdLow) / (rfuStdHigh - rfuStdLow)));
        }

        return new LookupTable(entries);
    }

    /// <summary>
    /// Creates a JSON lookup-table file from an RFU CSV file.
    /// </summary>
    public static LookupTable CreateJsonFromCsv(string csvPath, string jsonPath)
    {
        LookupTable lookupTable = FromCsv(csvPath);
        lookupTable.SaveJson(jsonPath);
        return lookupTable;
    }

    private static string GetColumnValue(string[] row, int index)
    {
        return index < row.Length ? row[index] : string.Empty;
    }
}
