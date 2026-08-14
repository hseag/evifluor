# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import argparse
import json
import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

from hse.evifluor.kits import Default as DefaultKit
from hse.evifluor import service


def _resolve_log_file(args):
    """Resolves the CLI log file path.

    Args:
        args: Parsed CLI arguments. ``working_dir`` is used when available.

    Returns:
        Absolute path to the CLI log file.
    """
    if hasattr(args, "working_dir") and args.working_dir is not None:
        log_dir = os.path.abspath(args.working_dir)
    else:
        log_dir = os.getcwd()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "evifluor.log")


def _configure_logging(args):
    """Configures logging for the CLI process.

    Args:
        args: Parsed CLI arguments controlling debug mode and working directory.
    """
    logger = logging.getLogger("hse.evifluor")

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(logging.DEBUG)

    if args.debug:
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = RotatingFileHandler(
            _resolve_log_file(args),
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def build_parser():
    """Builds the top-level argument parser for the CLI.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="python -m hse.evifluor",
        description="Command line interface for HSE eviFluor devices.",
    )
    parser.add_argument("--device", help="Device serial number, e.g. SN0010")
    parser.add_argument("--debug", action="store_true", help="Print full traceback on errors")

    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Show device information")
    info_parser.add_argument("--json", action="store_true", help="Print device information as JSON")

    selftest_parser = subparsers.add_parser("selftest", help="Run device selftest")
    selftest_parser.add_argument("--json", action="store_true", help="Print selftest result as JSON")
    selftest_parser.add_argument("--file", help="Write selftest output to file instead of stdout")

    subparsers.add_parser("checkempty", help="Check if the cuvette holder is empty")

    normalized_rfu_parser = subparsers.add_parser(
        "normalize-rfu-csv",
        help="Convert a result JSON file into a normalized RFU CSV",
    )
    normalized_rfu_parser.add_argument("json_file", help="Path to the result JSON file")
    normalized_rfu_parser.add_argument("replicates", type=int, help="Number of replicates per calibration block")
    normalized_rfu_parser.add_argument("--output", help="Output CSV path")

    run_parser = subparsers.add_parser("run", help="Manage measurement runs")
    run_parser.add_argument("--working-dir", default=".", help="Working directory (default: .)")
    run_parser.add_argument("--file", help="Data file")
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)

    run_init_parser = run_subparsers.add_parser("init", help="Initialize a run")
    run_init_parser.add_argument("nr_of_std_low", type=int, help="Number of standard-low measurements")
    run_init_parser.add_argument("nr_of_std_high", type=int, help="Number of standard-high measurements")
    run_init_parser.add_argument("concentration", type=float, help="Standard-high concentration")
    run_init_parser.add_argument("--kit", default="Default", help="Kit name (default: Default)")
    run_init_parser.add_argument("--k1", type=float, help="Optional kit parameter k1")
    run_init_parser.add_argument("--k2", type=float, help="Optional kit parameter k2")
    run_init_parser.add_argument("--k3", type=float, help="Optional kit parameter k3")
    run_init_parser.add_argument("--lookup_table", help="Optional lookup-table JSON file")
    run_init_parser.add_argument("--settling_time", type=float, help="Override settling time in seconds")
    run_init_parser.add_argument("--no-air", action="store_true", help="Initialize the run without air measurements")

    run_measure_parser = run_subparsers.add_parser("measure", help="Execute a measurement step")
    run_measure_parser.add_argument("comment", nargs="?", help="Optional measurement comment")

    run_subparsers.add_parser("export", help="Export the active run JSON file as CSV")

    return parser


def _write_output(text, filename=None):
    """Writes command output to stdout or a file.

    Args:
        text: Text content to write.
        filename: Optional destination filename. When omitted, the output is
            written to stdout.
    """
    if filename is not None:
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
        return

    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def cmd_info(args):
    """Handles the ``info`` command.

    Args:
        args: Parsed CLI arguments for the ``info`` command.

    Returns:
        Process exit code.
    """
    result = service.get_device_info(args.device)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("serialnumber: {}".format(result["serialnumber"]))
        print("firmwareVersion: {}".format(result["firmwareVersion"]))
        print("productionnumber: {}".format(result["productionnumber"]))
    return 0


def cmd_selftest(args):
    """Handles the ``selftest`` command.

    Args:
        args: Parsed CLI arguments for the ``selftest`` command.

    Returns:
        Process exit code. Non-zero indicates detected self-test problems.
    """
    payload = service.run_selftest(args.device)
    has_problems = payload["hasProblems"]

    if args.json:
        output = json.dumps(payload, indent=2)
    else:
        output = "\n".join([
            "selftest: {}".format("FAILED" if has_problems else "OK"),
            "result: {}".format(payload["result"]),
        ])

    _write_output(output, args.file)
    return 1 if has_problems else 0


def cmd_checkempty(args):
    """Handles the ``checkempty`` command.

    Args:
        args: Parsed CLI arguments for the ``checkempty`` command.

    Returns:
        Process exit code. Zero means the cuvette holder is empty.
    """
    if service.check_empty(args.device)["empty"]:
        print("Empty")
        return 0
    print("Not empty")
    return 1


def cmd_normalize_rfu_csv(args):
    """Handles the ``normalize-rfu-csv`` command.

    Args:
        args: Parsed CLI arguments containing the source JSON file and replicate
            count.

    Returns:
        Process exit code.
    """
    service.export_normalized_rfu_csv(
        args.json_file,
        args.replicates,
        csv_file=args.output,
    )
    return 0


def cmd_run(args):
    """Handles the ``run`` command group.

    Args:
        args: Parsed CLI arguments for run initialization, measurement, or
            export.

    Returns:
        Process exit code.
    """
    if args.run_command == "init":
        factory_kwargs = {}
        if args.k1 is not None:
            factory_kwargs["k1"] = args.k1
        if args.k2 is not None:
            factory_kwargs["k2"] = args.k2
        if args.k3 is not None:
            factory_kwargs["k3"] = args.k3
        if args.lookup_table is not None:
            factory_kwargs["lookup_table"] = args.lookup_table

        service.init_run(
            args.nr_of_std_low,
            args.nr_of_std_high,
            args.concentration,
            working_dir=args.working_dir,
            filename=args.file,
            device=args.device,
            no_air=args.no_air,
            kit=DefaultKit.factory(args.kit, **factory_kwargs),
            settling_time=args.settling_time,
        )
        return 0

    if args.run_command == "measure":
        service.measure_run(
            working_dir=args.working_dir,
            filename=args.file,
            device=args.device,
            comment=args.comment,
        )
        return 0

    service.export_run(
        working_dir=args.working_dir,
        filename=args.file,
        device=args.device,
    )
    return 0


def main(argv=None):
    """CLI entry point.

    Args:
        argv: Optional argument list. When omitted, arguments are read from
            ``sys.argv``.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args)

    try:
        if args.command == "info":
            return cmd_info(args)
        if args.command == "selftest":
            return cmd_selftest(args)
        if args.command == "checkempty":
            return cmd_checkempty(args)
        if args.command == "normalize-rfu-csv":
            return cmd_normalize_rfu_csv(args)
        return cmd_run(args)
    except Exception as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1
