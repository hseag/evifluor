# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

from hse.simulator.compare.evidense import compare_evidense_measurement
from hse.simulator.compare.evifluor import compare_evifluor_measurement
from hse.simulator.compare.shared import DotDict, load_json_file, trim_measurements


def compare_measurement_files(file_a, file_b, device, skip_a=0, skip_b=0, no_air=False) -> bool:
    data_a = load_json_file(file_a)
    data_b = load_json_file(file_b)

    trim_measurements(data_a, skip_a)
    trim_measurements(data_b, skip_b)

    if len(data_a.measurements) != len(data_b.measurements):
        print("Number of measurments differs!")
        print(f"    {file_a} : {len(data_a.measurements)}")
        print(f"    {file_b} : {len(data_b.measurements)}")
        return False

    matches = True
    for index in range(len(data_a.measurements)):
        measurement_a = DotDict(data_a.measurements[index])
        measurement_b = DotDict(data_b.measurements[index])
        if device == "evidense":
            if not compare_evidense_measurement(measurement_a, measurement_b, f"measurements[{index}]"):
                matches = False
        elif device == "evifluor":
            if not compare_evifluor_measurement(measurement_a, measurement_b, f"measurements[{index}]", no_air):
                matches = False
        else:
            print(f"Simulaor: Device ({device}) not supported")
            matches = False

    return matches


compare = compare_measurement_files

__all__ = ["compare", "compare_measurement_files"]
