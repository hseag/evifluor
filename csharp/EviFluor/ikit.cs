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
    double fit(Point stdLow, Point stdHigh, double value);
}

