// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Text.Json.Nodes;

namespace Hse.EviFluor;

/// <summary>
/// Represents a single measurement consisting the 470 nm wavelength channel.
/// </summary>
public class SingleMeasurement
{
    /// <summary>
    /// Gets or sets the channel for 470 nm measurements.
    /// </summary>
    public Channel Channel470 { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SingleMeasurement"/> class with optional channels.
    /// </summary>
    /// <param name="channel470">The channel for 470 nm (default: new Channel()).</param>
    public SingleMeasurement(Channel? channel470 = null)
    {
        Channel470 = channel470 ?? new Channel();
    }

    /// <summary>
    /// Returns a string representation of the measurement values.
    /// </summary>
    /// <returns>A formatted string containing all channel values.</returns>
    public override string ToString()
    {
        return $"470: [{Channel470}]]";
    }

    /// <summary>
    /// Converts the measurement data to a JSON representation.
    /// </summary>
    /// <returns>A JsonNode representing the measurement.</returns>
    public JsonNode ToJson()
    {
        return Channel470.ToJson();
    }


    /// <summary>
    /// Returns the difference between sample and dark.self->
    /// </summary>
    /// <returns>Difference between sample and dark</returns>
    public double Delta()
    {
        return Channel470.Delta();
    }

    /// <summary>
    /// Creates a <see cref="SingleMeasurement"/> instance from a JSON node.
    /// </summary>
    /// <param name="node">The JSON node containing measurement data.</param>
    /// <returns>A new <see cref="SingleMeasurement"/> instance.</returns>
    /// <exception cref="ArgumentNullException">Thrown if the JSON node is null or missing required properties.</exception>
    public static SingleMeasurement FromJson(JsonNode node)
    {
        if (node == null) throw new ArgumentNullException(nameof(node));

        return new SingleMeasurement(Channel.FromJson(node));
    }
}
