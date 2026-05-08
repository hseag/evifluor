# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import json
import math


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def load_json_file(filename):
    with open(filename, "rb") as handle:
        return DotDict(json.load(handle))


def compare_float(left, right, hint) -> bool:
    delta = 0.0000001
    matches = math.isclose(left, right, rel_tol=delta)
    if not matches:
        print(hint)
        print(f"    values differ {left} != {right}")
    return matches


def trim_measurements(data, skip_count):
    for _ in range(skip_count):
        if len(data.measurements) > 0:
            del data.measurements[0]
