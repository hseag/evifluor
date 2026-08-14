# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from enum import IntEnum

from .lookup_table import LookupTable

_KIT_FIT_ALGORITHM = "fitAlgorithm"
_KIT_SETTLING_TIME = "settlingTime"
_KIT_LOOKUP_TABLE = "lookupTable"
_KIT_STD_HIGH_TARGET_SIGNAL_FACTOR = "stdHighTargetSignalFactor"
_KIT_DESCRIPTION = "description"
_KIT_K1 = "k1"
_KIT_K2 = "k2"
_KIT_K3 = "k3"

class FitAlgorithm(IntEnum):
    """Supported post-calibration fit curves for kit-specific concentration mapping."""
    Linear                                        = 1
    LookupTable                                   = 2

class Default:
    """Base kit configuration combining standard interpolation with an optional fit curve."""

    def __init__(self, fit_algorithm = FitAlgorithm.Linear, k1 = 1.0, k2 = 0.0, k3 = 0.0, lookup_table = None, settling_time = 0.0, std_high_target_signal_factor = None, description = None):
        """Initializes a kit with explicit fit parameters and measurement behavior.

        Args:
            fit_algorithm: Fit model used to convert the calibrated signal into a
                concentration.
            k1: Primary scale factor applied to the fitted concentration.
            k2: Offset added to the fitted concentration after scaling.
            k3: Reserved third fit parameter for compatibility with existing kit
                definitions.
            lookup_table: Lookup table used when ``fit_algorithm`` is
                :class:`FitAlgorithm.LookupTable`.
            settling_time: Recommended settling time in seconds before taking a
                measurement.
            std_high_target_signal_factor: Optional target factor for the high
                standard signal during first-sample auto-gain.
            description: Human-readable description used for diagnostics and
                serialization.
        """
        try:
            self._fit_algorithm = FitAlgorithm(fit_algorithm)
        except ValueError as exc:
            raise ValueError("Unknown fit algorithm: {}".format(fit_algorithm)) from exc
        self._k1 = k1
        self._k2 = k2
        self._k3 = k3
        self._lookup_table = lookup_table
        self._settling_time = settling_time
        self._std_high_target_signal_factor = std_high_target_signal_factor
        self._description = description or "Default kit with linear fit"
        
    def __repr__(self):
        """Returns a textual description of the kit."""
        if self._fit_algorithm == FitAlgorithm.LookupTable:
            lookup_table_str = "None" if self._lookup_table is None else "present"
            return f"{self._description} fit_algorithm={self._fit_algorithm.name}, lookup_table={lookup_table_str}, settling_time={self._settling_time}, std_high_target_signal_factor={self._std_high_target_signal_factor}"
        else:
            return f"{self._description} fit_algorithm={self._fit_algorithm.name}, k1={self._k1}, k2={self._k2}, k3={self._k3}, settling_time={self._settling_time}, std_high_target_signal_factor={self._std_high_target_signal_factor}"

    def to_json(self):
        """Converts the kit configuration to a JSON representation."""
        return {
            _KIT_FIT_ALGORITHM: int(self._fit_algorithm),
            _KIT_K1: self._k1,
            _KIT_K2: self._k2,
            _KIT_K3: self._k3,
            _KIT_LOOKUP_TABLE: self._lookup_table,
            _KIT_SETTLING_TIME: self._settling_time,
            _KIT_STD_HIGH_TARGET_SIGNAL_FACTOR: self._std_high_target_signal_factor,
            _KIT_DESCRIPTION: self._description,
        }

    @staticmethod
    def factory(name, k1 = None, k2 = None, k3 = None, lookup_table = None):
        """Creates a predefined kit instance from a string name.

        Args:
            name: Preset kit name or alias.
            k1: Optional override for the primary scale factor.
            k2: Optional override for the additive concentration offset.
            k3: Optional override for the reserved third fit parameter.
            lookup_table: Optional lookup-table override for presets that support
                table-based fitting.

        Returns:
            The matching predefined or default kit instance.
        """
        name = name.lower()
        if name == "default":
            kwargs = {}
            if k1 is not None:
                kwargs["k1"] = k1
            if k2 is not None:
                kwargs["k2"] = k2
            if k3 is not None:
                kwargs["k3"] = k3
            if lookup_table is not None:
                kwargs["lookup_table"] = lookup_table
            return Default(**kwargs)
        if name == "qubittm_1x_dsdna_broad_range_br" or name == "qubit_br":
            kwargs = {}
            if k1 is not None:
                kwargs["k1"] = k1
            if k2 is not None:
                kwargs["k2"] = k2
            if k3 is not None:
                kwargs["k3"] = k3            
            if lookup_table is not None:
                kwargs["lookup_table"] = lookup_table
            return QubitTM_1X_dsDNA_Broad_Range_BR(**kwargs)
        if name == "qubittm_1x_dsdna_high_sensitivity_hs" or name == "qubit_hs":
            kwargs = {}
            if k1 is not None:
                kwargs["k1"] = k1
            if k2 is not None:
                kwargs["k2"] = k2
            if k3 is not None:
                kwargs["k3"] = k3
            return QubitTM_1X_dsDNA_High_Sensitivity_HS(**kwargs)

        raise ValueError("Unknown kit: {}".format(name))

    @staticmethod
    def from_json(node):
        """Creates a kit instance from a JSON node.

        Args:
            node: JSON object containing a serialized kit configuration.

        Returns:
            A deserialized :class:`Default` kit instance.
        """
        return Default(
            fit_algorithm = node[_KIT_FIT_ALGORITHM],
            k1 = node.get(_KIT_K1, 1.0),
            k2 = node.get(_KIT_K2, 0.0),
            k3 = node.get(_KIT_K3, 0.0),
            lookup_table = node.get(_KIT_LOOKUP_TABLE),
            settling_time = node.get(_KIT_SETTLING_TIME, 0.0),
            std_high_target_signal_factor = node.get(_KIT_STD_HIGH_TARGET_SIGNAL_FACTOR),
            description = node.get(_KIT_DESCRIPTION),
        )

    def fit(self, std_low, std_high, rfu):
        """Maps a measured signal to concentration using the configured fit model.

        Args:
            std_low: Low calibration standard used as the lower interpolation
                anchor.
            std_high: High calibration standard used as the upper interpolation
                anchor.
            rfu: Measured signal value to convert into a concentration.

        Returns:
            The calculated concentration for the measured signal.
        """
        # First interpolate between the two measured standards to get the raw concentration.
        delta_signal = std_high.value - std_low.value
        if delta_signal == 0:
            raise ValueError("Standard low and high must have different signal values for calibration")

        m = (std_high.concentration - std_low.concentration) / delta_signal
        b = std_high.concentration - m * std_high.value
        x = m * rfu + b
        
        # Then apply the kit-specific correction curve on top of the raw interpolation result.
        if self._fit_algorithm == FitAlgorithm.Linear:
            x_fitted = x * self._k1 + self._k2
        elif self._fit_algorithm == FitAlgorithm.LookupTable:
            if not self._lookup_table:
                raise ValueError("Lookup table fit algorithm requires a non-empty lookup table")

            lookup_table = sorted(self._lookup_table, key = lambda point: point["signal"])
            if len(lookup_table) == 1:
                x_fitted = lookup_table[0]["concentration"]
            else:
                rfu_norm = (rfu - std_low.value) / delta_signal

                lower = lookup_table[0]
                upper = lookup_table[1]
                for candidate_lower, candidate_upper in zip(lookup_table, lookup_table[1:]):
                    lower = candidate_lower
                    upper = candidate_upper
                    if rfu_norm <= upper["signal"]:
                        break

                delta_lookup_signal = upper["signal"] - lower["signal"]
                if delta_lookup_signal == 0:
                    raise ValueError("Lookup table signal values must be strictly monotonic")

                fraction = (rfu_norm - lower["signal"]) / delta_lookup_signal
                x_fitted = (lower["concentration"] + fraction * (upper["concentration"] - lower["concentration"])) * self._k1 + self._k2
        else:
            raise ValueError("Unknown fit algorithm: {}".format(self._fit_algorithm))
        
        return x_fitted
    
    def settling_time(self):
        """Returns the time in seconds to wait after adding the reagent before measuring."""
        return self._settling_time

    def std_high_target_signal_factor(self):
        """Returns the autogain factor for the high standard signal."""
        return self._std_high_target_signal_factor

class QubitTM_1X_dsDNA_High_Sensitivity_HS(Default):
    """Preset for the QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit."""

    def __init__(self, k1 = 1.0, k2 = 0.0):
        """Initializes the QubitTM 1X dsDNA High Sensitivity preset.

        Args:
            k1: Optional override for the preset's primary scale factor.
            k2: Optional override for the preset's additive concentration offset.
        """
        super().__init__(fit_algorithm = FitAlgorithm.Linear, k1 = k1, k2 = k2, description = "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit", settling_time = 0.0)
        pass

class QubitTM_1X_dsDNA_Broad_Range_BR(Default):
    """Preset for the QubitTM 1X dsDNA Broad Range (BR) Assay Kit."""

    def __init__(self, k1 = 1.0, k2 = 0.0, lookup_table = None):
        """Initializes the QubitTM 1X dsDNA Broad Range preset.

        Args:
            k1: Optional override for the preset's primary scale factor.
            k2: Optional override for the preset's additive concentration offset.
            lookup_table: Optional replacement for the preset lookup table. This
                can be a list of lookup-table entries or a CSV/JSON file path.
        """
        if lookup_table is None:
            lookup_table = [
                {
                  "concentration": 0.0,
                  "signal": 8.21960772015573e-19
                },
                {
                  "concentration": 0.655,
                  "signal": 0.005511528146509457
                },
                {
                  "concentration": 1.15,
                  "signal": 0.012096556749881238
                },
                {
                  "concentration": 10.3,
                  "signal": 0.11696146388117148
                },
                {
                  "concentration": 42.9,
                  "signal": 0.4437930749162957
                },
                {
                  "concentration": 80.5,
                  "signal": 0.8584075257182888
                },
                {
                  "concentration": 100.0,
                  "signal": 1.0
                },
                {
                  "concentration": 101.0,
                  "signal": 1.029219428556792
                },
                {
                  "concentration": 166.0,
                  "signal": 1.4952711926922733
                },
                {
                  "concentration": 242.0,
                  "signal": 1.9368286353950304
                }
            ]
        else:
            if not isinstance(lookup_table, list):
                lookup_table = LookupTable.load(lookup_table).to_json()
                                
        super().__init__(fit_algorithm = FitAlgorithm.LookupTable, k1 = k1, k2 = k2, lookup_table = lookup_table, description = "QubitTM 1X dsDNA Broad Range (BR) Assay Kit", std_high_target_signal_factor = 0.4, settling_time = 0.0)
        pass
