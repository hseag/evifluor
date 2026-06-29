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
    if hasattr(args, "working_dir") and args.working_dir is not None:
        log_dir = os.path.abspath(args.working_dir)
    else:
        log_dir = os.getcwd()
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "evifluor.log")


def _configure_logging(args):
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

    run_parser = subparsers.add_parser("run", help="Manage measurement runs")
    run_parser.add_argument("--working-dir", default=".", help="Working directory (default: .)")
    run_parser.add_argument("--file", help="Data file")
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)

    run_init_parser = run_subparsers.add_parser("init", help="Initialize a run")
    run_init_parser.add_argument("nr_of_std_low", type=int, help="Number of standard-low measurements")
    run_init_parser.add_argument("nr_of_std_high", type=int, help="Number of standard-high measurements")
    run_init_parser.add_argument("concentration", type=float, help="Standard-high concentration")
    run_init_parser.add_argument("--kit", default="Default", help="Kit name (default: Default)")
    run_init_parser.add_argument("--settling_time", type=float, help="Override settling time in seconds")
    run_init_parser.add_argument("--no-air", action="store_true", help="Initialize the run without air measurements")

    run_measure_parser = run_subparsers.add_parser("measure", help="Execute a measurement step")
    run_measure_parser.add_argument("comment", nargs="?", help="Optional measurement comment")

    run_subparsers.add_parser("export", help="Export the active run JSON file as CSV")

    return parser


def _write_output(text, filename=None):
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
    result = service.get_device_info(args.device)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("serialnumber: {}".format(result["serialnumber"]))
        print("firmwareVersion: {}".format(result["firmwareVersion"]))
        print("productionnumber: {}".format(result["productionnumber"]))
    return 0


def cmd_selftest(args):
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
    if service.check_empty(args.device)["empty"]:
        print("Empty")
        return 0
    print("Not empty")
    return 1


def cmd_run(args):
    if args.run_command == "init":
        service.init_run(
            args.nr_of_std_low,
            args.nr_of_std_high,
            args.concentration,
            working_dir=args.working_dir,
            filename=args.file,
            device=args.device,
            no_air=args.no_air,
            kit=DefaultKit.factory(args.kit),
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
        return cmd_run(args)
    except Exception as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1
