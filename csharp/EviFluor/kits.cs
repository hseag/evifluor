// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;

namespace Hse.EviFluor.Kits;

/// <summary>
/// Default implementation of the IKit interface using linear interpolation.
/// </summary>
public class Default : IKit
{
    /// <summary>
    /// Creates a linear interpolation kit using two standard points (low/high).
    /// </summary>
    public Default()
     { 
     }

    /// <summary>
    /// Returns a textual description of the default kit.
    /// </summary>
    /// <returns>Kit description string.</returns>
    public override string ToString()
    {
        return "Default kit with linear interpolation between std low and std high";
    }

    /// <inheritdoc/>
    /// <remarks>
    /// Throws <see cref="DivideByZeroException"/> if <c>stdHigh.Value == stdLow.Value</c>.
    /// Callers should ensure distinct calibration signals.
    /// </remarks> 
    public double fit(Point stdLow, Point stdHigh, double value)
     {
        var m = (stdHigh.Concentration - stdLow.Concentration) / (stdHigh.Value - stdLow.Value);
        var b = stdHigh.Concentration - m * stdHigh.Value;
        return m * value + b;
    }
}

/// <summary>
/// Linear kit preset for Thermo Fisher Quant-iT™ dsDNA HS Assay (Q33120).
/// </summary>
public class Quant_iT_dsDNA_HS : Default
{
    /// <summary>
    /// Linear kit preset for Thermo Fisher Quant-iT™ dsDNA HS Assay (Q33120).
    /// </summary>
    public Quant_iT_dsDNA_HS()
    {
    }

    /// <summary>
    /// Returns a textual description of this specific kit.
    /// </summary>
    /// <returns>Kit description string.</returns>
    public override string ToString()
    {
        return "Quant-iT dsDNA Assay Kit, High Sensitivity (Q33120)";
    }
}