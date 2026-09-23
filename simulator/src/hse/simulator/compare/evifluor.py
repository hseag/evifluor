# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

from hse.simulator.compare.shared import DotDict, compare_float


def compare_evifluor_results(left, right, hint) -> bool:
    matches = True
    if not compare_float(left.concentration, right.concentration, hint + "/concentration"):
        matches = False
    if not compare_float(left.rfu, right.rfu, hint + "/rfu"):
        matches = False
    return matches


def compare_evifluor_single_measurement(left, right, hint) -> bool:
    matches = True
    if not compare_float(left.dark, right.dark, hint + "/dark"):
        matches = False
    if not compare_float(left.value, right.value, hint + "/value"):
        matches = False
    if not compare_float(left.ledPower, right.ledPower, hint + "/ledPower"):
        matches = False
    return matches


def compare_evifluor_measurement(left, right, hint) -> bool:
    matches = True

    if left.results is None or right.results is None:
        print(hint)
        print("    entry results missing")
        matches = False
    elif not compare_evifluor_results(DotDict(left.results), DotDict(right.results), hint + "/results"):
        matches = False

    if left.air is None and right.air is None:
        pass
    elif left.air is None or right.air is None:
        print(hint)
        print("    entry air differs")
        matches = False
    elif not compare_evifluor_single_measurement(DotDict(left.air), DotDict(right.air), hint + "/air"):
        matches = False

    if left.sample is None or right.sample is None:
        print(hint)
        print("    entry sample missing")
        matches = False
    elif not compare_evifluor_single_measurement(DotDict(left.sample), DotDict(right.sample), hint + "/sample"):
        matches = False

    if left.errors is None and right.errors is None:
        pass
    elif left.errors is not None and right.errors is not None:
        pass
    else:
        print(hint)
        print("    entry errors differs")
        matches = False

    return matches
