# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

class Default:
    """Default kit implementation using linear interpolation between standards."""

    def __init__(self):
        """Creates a linear interpolation kit using two standard points."""
        pass
        
    def __repr__(self):
        """Returns a textual description of the default kit."""
        return "Default kit with linear interpolation between std low and std high"
        
    def fit(self, std_low, std_high, value):
        """Fits a value using linear interpolation between standard low and high."""
        m = (std_high.concentration - std_low.concentration) / (std_high.value - std_low.value)
        b = std_high.concentration - m * std_high.value
        return m * value + b
        

class Quant_iT_dsDNA_HS(Default):
    """Linear kit preset for the Thermo Fisher Quant-iT dsDNA HS Assay (Q33120)."""

    def __init__(self):
        """Initializes the Quant-iT dsDNA HS kit preset."""
        pass
    
    def __repr__(self):
        """Returns a textual description of this specific kit."""
        return "Quant-iT dsDNA Assay Kit, High Sensitivity (Q33120)"
