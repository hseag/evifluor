# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import argparse

from hse.simulator.control import SimulationControl
from hse.simulator.evidense import EviDenseSimulation
from hse.simulator.evifluor import EviFluorSimulation
from hse.simulator.web import WebServerHandle


def build_parser():
    parser = argparse.ArgumentParser(description="eviFamily simulator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    parser.add_argument("--no-web", action="store_true", help="Do not start the web UI")
    parser.add_argument("--web-host", default="127.0.0.1", help="Bind host for the web UI")
    parser.add_argument("--web-port", type=int, help="Bind port for the web UI")

    subparsers = parser.add_subparsers(dest="mode", required=True, help="Mode")

    evidense_parser = subparsers.add_parser("evidense", help="eviDense simulation")
    evidense_parser.add_argument("data", nargs="?", help="Data file to use (optional)")

    evifluor_parser = subparsers.add_parser("evifluor", help="eviFluor simulation")
    evifluor_parser.add_argument("--no-air", action="store_true", help="Run without air correction")
    evifluor_parser.add_argument("data", nargs="?", help="Data file to use (optional)")

    sim_parser = subparsers.add_parser("sim", help="Simulation control")
    sim_parser.add_argument("commands", nargs=argparse.REMAINDER, help="Simulation commands")
    return parser


def create_simulation(args):
    if args.mode == "evidense":
        return EviDenseSimulation(), "evidense"
    if args.mode == "evifluor":
        return EviFluorSimulation(args.no_air), "evifluor"
    raise Exception("Device not implemented!")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    print(args)

    if args.mode == "sim":
        SimulationControl.send(args.commands)
        return 0

    simulation, web_device = create_simulation(args)
    if args.data is not None:
        simulation.load_data(args.data)

    web = None
    try:
        if not args.no_web:
            web = WebServerHandle()
            web_url = web.start(web_device, host=args.web_host, port=args.web_port)
            print(f"Started {simulation.device_name()} web UI at {web_url}")

        print(f"Starting simulation for {simulation.device_name()}")
        simulation.start_server(args.verbose)
    except KeyboardInterrupt:
        print("Simulation stopped")
        simulation.stop()
    finally:
        simulation.stop()
        if web is not None:
            web.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
