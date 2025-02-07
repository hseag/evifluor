// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Text.Json.Nodes;

namespace Hse.EviFluor;

/// <summary>
/// Represents a measurement channel with sample and reference values, measured in mV.
/// </summary>
public class Channel
{
    /// <summary>
    /// Gets or sets the dark value in mV.
    /// </summary>
    public double Dark { get; set; }

    /// <summary>
    /// Gets or sets the value in mV.
    /// </summary>
    public double Value { get; set; }

    /// <summary>
    /// Gets or sets the led power. No unit, range 0..255..
    /// </summary>
    public int LedPower { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Channel"/> class with optional dark and value values.
    /// </summary>
    /// <param name="dark">The dark value in mV (default: 0.0).</param>
    /// <param name="value">The value in mV (default: 0.0).</param>
    /// <param name="ledPower">The led power, no unit, range 0..255 (default: 0).</param>
    public Channel(double dark = 0.0, double value = 0.0, int ledPower = 0)
    {
        Dark = dark;
        Value = value;
        LedPower = ledPower;
    }

    /// <summary>
    /// Returns a string representation of the channel values.
    /// </summary>
    /// <returns>A string in the format "Sample: [value] Reference: [value]".</returns>
    public override string ToString()
    {
        return $"Dark:{Dark} Value:{Value} LedPower:{LedPower}";
    }

    /// <summary>
    /// Calculates the difference between value and dark.
    /// </summary>
    /// <returns>difference in mV</returns>
    public double Delta()
    {
        return Value - Dark;
    }

    /// <summary>
    /// Converts the channel values to a JSON representation.
    /// </summary>
    /// <returns>A JsonNode representing the channel values.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();
        obj[Dict.DARK] = JsonValue.Create(Dark);
        obj[Dict.VALUE] = JsonValue.Create(Value);
        obj[Dict.LED_POWER] = JsonValue.Create(LedPower);

        return obj;
    }

    /// <summary>
    /// Creates a <see cref="Channel"/> instance from a JSON node.
    /// </summary>
    /// <param name="node">The JSON node containing the channel data.</param>
    /// <returns>A new <see cref="Channel"/> instance with values extracted from the JSON node.</returns>
    /// <exception cref="ArgumentException">Thrown when the JSON node is invalid.</exception>
    public static Channel FromJson(JsonNode node)
    {
        if (node is JsonObject jsonObject &&
            jsonObject.TryGetPropertyValue(Dict.DARK, out JsonNode? darkNode) &&
            jsonObject.TryGetPropertyValue(Dict.VALUE, out JsonNode? valueNode) &&
            jsonObject.TryGetPropertyValue(Dict.LED_POWER, out JsonNode? ledPowerNode) &&
            darkNode is not null &&
            valueNode is not null &&
            ledPowerNode is not null)
        {
            return new Channel(darkNode.GetValue<double>(), valueNode.GetValue<double>(), ledPowerNode.GetValue<int>());
        }
        else
        {
            throw new ArgumentException("Invalid JSON node for Channel.");
        }
    }
}
