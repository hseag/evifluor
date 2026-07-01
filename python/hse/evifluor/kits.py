# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from enum import IntEnum


_KIT_FIT_ALGORITHM = "fitAlgorithm"
_KIT_K1 = "k1"
_KIT_K2 = "k2"
_KIT_K3 = "k3"
_KIT_SETTLING_TIME = "settlingTime"
_KIT_STD_HIGH_TARGET_SIGNAL_FACTOR = "stdHighTargetSignalFactor"
_KIT_DESCRIPTION = "description"


class FitAlgorithm(IntEnum):
    """Supported post-calibration fit curves for kit-specific concentration mapping."""
    Linear                                        = 1
    Power                                         = 2
    Quadratic                                     = 3
    HillFit                                       = 4

class Default:
    """Base kit configuration combining standard interpolation with an optional fit curve."""

    def __init__(self, fit_algorithm = FitAlgorithm.Linear, k1 = 1.0, k2 = 0.0, k3 = 0.0, settling_time = 0.0, std_high_target_signal_factor = None, description = None):
        try:
            self._fit_algorithm = FitAlgorithm(fit_algorithm)
        except ValueError as exc:
            raise ValueError("Unknown fit algorithm: {}".format(fit_algorithm)) from exc
        self._k1 = k1
        self._k2 = k2
        self._k3 = k3
        self._settling_time = settling_time
        self._std_high_target_signal_factor = std_high_target_signal_factor
        self._description = description or "Default kit with linear fit"
        
    def __repr__(self):
        """Returns a textual description of the kit."""
        return f"{self._description} fit_algorithm={self._fit_algorithm.name}, k1={self._k1}, k2={self._k2}, k3={self._k3}, settling_time={self._settling_time}, std_high_target_signal_factor={self._std_high_target_signal_factor}"

    def to_json(self):
        """Converts the kit configuration to a JSON representation."""
        return {
            _KIT_FIT_ALGORITHM: int(self._fit_algorithm),
            _KIT_K1: self._k1,
            _KIT_K2: self._k2,
            _KIT_K3: self._k3,
            _KIT_SETTLING_TIME: self._settling_time,
            _KIT_STD_HIGH_TARGET_SIGNAL_FACTOR: self._std_high_target_signal_factor,
            _KIT_DESCRIPTION: self._description,
        }

    @staticmethod
    def factory(name):
        """Creates a predefined kit instance from a string name."""
        name = name.lower()

        if name == "default":
            return Default()
        if name == "qubittm_1x_dsdna_broad_range_br" or name == "qubit_br":
            return QubitTM_1X_dsDNA_Broad_Range_BR()
        if name == "qubittm_1x_dsdna_high_sensitivity_hs" or name == "qubit_hs":
            return QubitTM_1X_dsDNA_High_Sensitivity_HS()

        raise ValueError("Unknown kit: {}".format(name))

    @staticmethod
    def from_json(node):
        """Creates a kit instance from a JSON node."""
        return Default(
            fit_algorithm = node[_KIT_FIT_ALGORITHM],
            k1 = node[_KIT_K1],
            k2 = node[_KIT_K2],
            k3 = node.get(_KIT_K3, 0.0),
            settling_time = node.get(_KIT_SETTLING_TIME, 0.0),
            std_high_target_signal_factor = node.get(_KIT_STD_HIGH_TARGET_SIGNAL_FACTOR),
            description = node.get(_KIT_DESCRIPTION),
        )

    def fit(self, std_low, std_high, rfu):
        """Maps a measured signal to concentration using the calibrated standards and fit curve."""
        # First interpolate between the two measured standards to get the raw concentration.
        delta_signal = std_high.value - std_low.value
        if delta_signal == 0:
            raise ValueError("Standard low and high must have different signal values for calibration")

        m = (std_high.concentration - std_low.concentration) / delta_signal
        b = std_high.concentration - m * std_high.value
        x = m * rfu + b
        
        # Then apply the kit-specific correction curve on top of the raw interpolation result.
        if self._fit_algorithm == FitAlgorithm.Linear:
            x_fitted = self._k1 * x + self._k2
        elif self._fit_algorithm == FitAlgorithm.Power:
            # Negative concentrations are clamped to zero before exponentiation.
            if x < 0:
                x_fitted = 0
            else:
                x_fitted = self._k1 * x ** self._k2
        elif self._fit_algorithm == FitAlgorithm.Quadratic:
            # Negative concentrations are clamped to zero before the quadratic correction.
            if x < 0:
                x_fitted = 0
            else:
                x_fitted = self._k1 * x ** 2 + self._k2 * x + self._k3
        elif self._fit_algorithm == FitAlgorithm.HillFit:
            # Negative concentrations are clamped to zero before the correction.
            # k1 : VMAX
            # k2 : K
            # k3 : n
            
            num = std_high.value * (std_high.concentration - std_low.concentration)
            den = (std_high.concentration - std_low.concentration) ** 2

            if den == 0:
                raise ValueError("All concentrations are zero")

            S = num / den
            
            if rfu < 0:
                x_fitted = 0
            else:
                x = rfu / S
                x_fitted = (self._k1 * x ** self._k3) / (self._k2 ** self._k3 + x ** self._k3)
        return x_fitted
    
    def settling_time(self):
        """Returns the time in seconds to wait after adding the reagent before measuring."""
        return self._settling_time

    def std_high_target_signal_factor(self):
        """Returns the autogain factor for the high standard signal."""
        return self._std_high_target_signal_factor

class QubitTM_1X_dsDNA_High_Sensitivity_HS(Default):
    """Preset for the QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit."""

    def __init__(self):
        """Initializes the QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit preset."""
        super().__init__(fit_algorithm = FitAlgorithm.Linear, k1 = 1.0, k2 = 0.0, description = "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit", settling_time = 0.0)
        pass

class QubitTM_1X_dsDNA_Broad_Range_BR(Default):
    """Preset for the QubitTM 1X dsDNA Broad Range (BR) Assay Kit."""

    def __init__(self):
        super().__init__(fit_algorithm = FitAlgorithm.HillFit, k1 = 52452044.021155454, k2 = 3342216.695097067 , k3 = 1.2623036398450653, description = "QubitTM 1X dsDNA Broad Range (BR) Assay Kit", std_high_target_signal_factor = 0.4, settling_time = 0.0)
        pass
