# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

import csv
import json
import os


class LookupTable:
    """Stores lookup table points and converts between CSV and JSON representations."""

    def __init__(self, entries = None):
        """Initializes the lookup table with optional point entries.

        Args:
            entries: Iterable of lookup-table entries containing ``concentration``
                and ``signal`` values. Defaults to an empty table.
        """
        if entries is None:
            entries = []
        self.entries = sorted(
            [self._normalize_entry(entry) for entry in entries],
            key = lambda entry: entry["signal"],
        )

    def __repr__(self):
        """Returns a debug representation of the lookup table."""
        return "LookupTable(entries={})".format(self.entries)

    def to_json(self):
        """Returns the lookup table as a JSON-serializable list."""
        return [
            {
                "concentration": entry["concentration"],
                "signal": entry["signal"],
            }
            for entry in self.entries
        ]

    def save_json(self, json_path):
        """Writes the lookup table to a JSON file.

        Args:
            json_path: Destination path for the JSON file.
        """
        with open(json_path, "w", encoding = "utf-8") as handle:
            json.dump(self.to_json(), handle, indent = 2)

    @classmethod
    def load(cls, path):
        """Loads a lookup table from a CSV or JSON file.

        Args:
            path: Source file path. The extension decides whether CSV or JSON
                loading is used.

        Returns:
            A populated :class:`LookupTable` instance.
        """
        _, extension = os.path.splitext(path)
        extension = extension.lower()

        if extension == ".json":
            return cls.load_json(path)
        if extension == ".csv":
            return cls.from_csv(path)

        raise ValueError("Unsupported lookup table file extension: {}".format(extension or "<none>"))

    @classmethod
    def load_json(cls, json_path):
        """Loads a lookup table from a JSON file.

        Args:
            json_path: Path to a JSON file containing a lookup-table list or a
                wrapper object with ``lookupTable``.

        Returns:
            A populated :class:`LookupTable` instance.
        """
        with open(json_path, "r", encoding = "utf-8") as handle:
            data = json.load(handle)

        if isinstance(data, dict):
            data = data.get("lookupTable")

        if not isinstance(data, list):
            raise ValueError("Lookup table JSON must contain a list of entries")

        return cls(data)

    @classmethod
    def from_csv(cls, csv_path):
        """Builds a lookup table from a CSV file.

        Args:
            csv_path: Path to a CSV file containing ``RFU`` and
                ``Concentration``. The first data row is interpreted as
                ``std high`` and the second data row as ``std low`` to derive
                normalized signal values.

        Returns:
            A populated :class:`LookupTable` instance.
        """
        rows = []
        with open(csv_path, "r", encoding = "utf-8", newline = "") as handle:
            reader = csv.DictReader(handle, delimiter = ";")

            if reader.fieldnames is None:
                raise ValueError("CSV file is empty")

            required_columns = {"RFU", "Concentration"}
            missing_columns = required_columns.difference(reader.fieldnames)
            if missing_columns:
                raise ValueError("CSV file is missing columns: {}".format(", ".join(sorted(missing_columns))))

            for row_index, row in enumerate(reader, start = 2):
                concentration_text = (row.get("Concentration") or "").strip()
                rfu_text = (row.get("RFU") or "").strip()

                if rfu_text == "" and concentration_text == "":
                    continue

                if concentration_text == "" or rfu_text == "":
                    raise ValueError("CSV row {} must contain RFU and Concentration".format(row_index))

                rows.append({
                    "concentration": float(concentration_text),
                    "rfu": float(rfu_text),
                })

        if len(rows) < 2:
            raise ValueError("CSV file must contain at least two data rows to derive RFU normalization")

        rfu_std_high = rows[0]["rfu"]
        rfu_std_low = rows[1]["rfu"]
        if rfu_std_high == rfu_std_low:
            raise ValueError("RFU standard high and standard low must be different")

        entries = [
            {
                "concentration": row["concentration"],
                "signal": (row["rfu"] - rfu_std_low) / (rfu_std_high - rfu_std_low),
            }
            for row in rows
        ]

        return cls(entries)

    @classmethod
    def create_json_from_csv(cls, csv_path, json_path):
        """Creates a JSON lookup-table file from an RFU CSV file.

        Args:
            csv_path: Path to the RFU CSV file.
            json_path: Destination path for the generated JSON file.

        Returns:
            The created :class:`LookupTable` instance.
        """
        lookup_table = cls.from_csv(csv_path)
        lookup_table.save_json(json_path)
        return lookup_table

    @staticmethod
    def _normalize_entry(entry):
        """Normalizes a lookup-table entry to the expected internal schema.

        Args:
            entry: Mapping containing ``concentration`` and ``signal``.

        Returns:
            A normalized dictionary with floating-point values.
        """
        if not isinstance(entry, dict):
            raise ValueError("Lookup table entries must be objects")

        if "concentration" not in entry or "signal" not in entry:
            raise ValueError("Lookup table entries must contain concentration and signal")

        return {
            "concentration": float(entry["concentration"]),
            "signal": float(entry["signal"]),
        }
