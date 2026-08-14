# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import socket

from hse.simulator.base import SIMULATOR_PORT


class SimulationControl:
    @staticmethod
    def send(txs, host="127.0.0.1", port=SIMULATOR_PORT):
        if isinstance(txs, list):
            tx = " ".join(txs)
        else:
            tx = txs
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
                if not tx.startswith(":"):
                    tx = ":! " + tx
                if not tx.endswith("\n"):
                    tx += "\n"
                sock.sendall(tx.encode())

                response = b""
                while not response.endswith(b"\n"):
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response += chunk

                if response != b":! 0":
                    print("Response:", response.decode().strip())
                return response.decode().strip()
        except ConnectionRefusedError:
            print("No connection?")
        except Exception as exc:
            print("Send error:", exc)


simulation_control = SimulationControl
