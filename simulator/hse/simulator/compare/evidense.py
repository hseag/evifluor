# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

from hse.simulator.compare.shared import DotDict, compare_float


def compare_evidense_results(left, right, hint) -> bool:
    matches = True
    if not compare_float(left.dsDNA, right.dsDNA, hint + "/dsDNA"):
        matches = False
    if not compare_float(left.ssDNA, right.ssDNA, hint + "/ssDNA"):
        matches = False
    if not compare_float(left["purity260/230"], right["purity260/230"], hint + "/purity260/230"):
        matches = False
    if not compare_float(left["purity260/280"], right["purity260/280"], hint + "/purity260/280"):
        matches = False
    if not compare_float(left["A230"], right["A230"], hint + "/A230"):
        matches = False
    if not compare_float(left["A260"], right["A260"], hint + "/A260"):
        matches = False
    if not compare_float(left["A280"], right["A280"], hint + "/A280"):
        matches = False
    if not compare_float(left["A340"], right["A340"], hint + "/A340"):
        matches = False
    return matches


def compare_evidense_single_channel(left, right, hint) -> bool:
    matches = True
    if not compare_float(left.sample, right.sample, hint + "/sample"):
        matches = False
    if not compare_float(left.reference, right.reference, hint + "/reference"):
        matches = False
    return matches


def compare_evidense_single_measurement(left, right, hint) -> bool:
    matches = True
    if not compare_evidense_single_channel(DotDict(left["230"]), DotDict(right["230"]), hint + "/230"):
        matches = False
    if not compare_evidense_single_channel(DotDict(left["260"]), DotDict(right["260"]), hint + "/260"):
        matches = False
    if not compare_evidense_single_channel(DotDict(left["280"]), DotDict(right["280"]), hint + "/280"):
        matches = False
    if not compare_evidense_single_channel(DotDict(left["340"]), DotDict(right["340"]), hint + "/340"):
        matches = False
    return matches


def compare_evidense_measurement(left, right, hint) -> bool:
    matches = True

    if left.results is None or right.results is None:
        print(hint)
        print("    entry results missing")
        matches = False
    elif not compare_evidense_results(DotDict(left.results), DotDict(right.results), hint + "/results"):
        matches = False

    if left.baseline is None or right.baseline is None:
        print(hint)
        print("    entry baseline missing")
        matches = False
    elif not compare_evidense_single_measurement(DotDict(left.baseline), DotDict(right.baseline), hint + "/baseline"):
        matches = False

    if left.air is None or right.air is None:
        print(hint)
        print("    entry air missing")
        matches = False
    elif not compare_evidense_single_measurement(DotDict(left.air), DotDict(right.air), hint + "/air"):
        matches = False

    if left.sample is None or right.sample is None:
        print(hint)
        print("    entry sample missing")
        matches = False
    elif not compare_evidense_single_measurement(DotDict(left.sample), DotDict(right.sample), hint + "/sample"):
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
