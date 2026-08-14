# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

import csv
import json
import os

from .constants import DictKeys


class NormalizedRfuCsvExporter:
    """Exports measurement comments grouped by replicate blocks."""

    def __init__(self, json_path, replicates):
        """Initializes a normalized-RFU CSV exporter.

        Args:
            json_path: Source measurement JSON file.
            replicates: Number of replicates per calibration block.
        """
        self._json_path = json_path
        self._replicates = replicates

        if self._replicates <= 0:
            raise ValueError("replicates must be greater than zero")

    def export(self, csv_path = None):
        """Writes the CSV export and returns its path.

        Args:
            csv_path: Optional destination CSV path. When omitted, a filename is
                derived from ``json_path``.

        Returns:
            Path to the generated CSV file.
        """
        data = self._load_data()
        measurements = data.get(DictKeys.MEASUREMENTS, [])

        if csv_path is None:
            filename_base, _ = os.path.splitext(self._json_path)
            csv_path = f"{filename_base}_normalized_rfu.csv"

        with open(csv_path, "w", newline = "", encoding = "utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter = ";")
            writer.writerow(["Comment", "Concentration"])

            for block in self._measurement_blocks(measurements):
                comment = block[0].get(DictKeys.COMMENT, "")
                writer.writerow([comment, ""])

        return csv_path

    def _load_data(self):
        """Loads and returns the source JSON document.

        Returns:
            Parsed JSON content of the source file.
        """
        if not os.path.isfile(self._json_path):
            raise FileNotFoundError("File {} not found".format(self._json_path))

        with open(self._json_path, "r", encoding = "utf-8") as handle:
            return json.load(handle)

    def _measurement_blocks(self, measurements):
        """Splits the measurements into consecutive replicate blocks.

        Args:
            measurements: Sequence of serialized measurement entries.

        Yields:
            Consecutive blocks of measurements with ``replicates`` items each.
        """
        for start in range(0, len(measurements), self._replicates):
            block = measurements[start:start + self._replicates]
            if len(block) > 0:
                yield block
