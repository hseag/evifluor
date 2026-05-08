# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import shlex
import socket


def send_command(command: str, host: str = "127.0.0.1", port: int = 5000) -> list[str]:
    tx = command if command.startswith(":") else f":{command}"
    if not tx.endswith("\n"):
        tx += "\n"

    with socket.create_connection((host, port), timeout=5) as conn:
        conn.sendall(tx.encode("utf-8"))

        response = b""
        while not response.endswith(b"\n"):
            chunk = conn.recv(1024)
            if not chunk:
                break
            response += chunk

    if not response:
        raise RuntimeError("No response from simulator")
    if response[0:1] != b":":
        raise RuntimeError(f"Invalid simulator response: {response!r}")

    parts = shlex.split(response[1:].decode("utf-8").strip())
    if not parts:
        raise RuntimeError("Empty simulator response")
    if parts[0] == "E":
        raise RuntimeError(f"Simulator returned error {parts[1]}")
    return parts
