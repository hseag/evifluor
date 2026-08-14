# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import argparse

from hse.simulator.compare import compare_measurement_files


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("device", choices=["evidense", "evifluor"], help="Device to compare")
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--no-air", help="Expect eviFluor measurements without air field", action="store_true")
    parser.add_argument("--skip-a", help="Skip first N measurements from file a", default=0, type=int)
    parser.add_argument("--skip-b", help="Skip first N measurements from file b", default=0, type=int)
    parser.add_argument("a")
    parser.add_argument("b")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    same = compare_measurement_files(
        args.a,
        args.b,
        args.device,
        skip_a=args.skip_a,
        skip_b=args.skip_b,
        no_air=args.no_air,
    )
    if same:
        print(f"file {args.a} and {args.b} are the same.")
        return 0

    print(f"file {args.a} and {args.b} differ!.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
