// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

namespace Hse.EviFluor;

/// <summary>
/// Interface for implementing calibration fitting algorithms.
/// </summary>
public interface IKit
{
    /// <summary>
    /// Performs a calibration fit using two standard reference points.
    /// </summary>
    /// <param name="stdLow">Low concentration standard point.</param>
    /// <param name="stdHigh">High concentration standard point.</param>
    /// <param name="value">The raw measured value to convert.</param>
    /// <returns>Calculated concentration based on interpolation.</returns>
    /// <remarks>
    /// Implementations may assume that <paramref name="stdLow"/> and <paramref name="stdHigh"/> define a valid
    /// calibration range and that the measured signal increases monotonically with concentration.
    /// Units of <see cref="Point.Concentration"/> are kit-specific.
    /// </remarks>
    ///
    double fit(Point stdLow, Point stdHigh, double value);
}

