# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import threading
import time


def _resolve_app_factory(device: str):
    if device == "evifluor":
        from hse.simulator.evifluor.web import create_app

        return create_app, 8010
    if device == "evidense":
        from hse.simulator.evidense.web import create_app

        return create_app, 8011
    raise ValueError(f"Unsupported simulator web device: {device}")


class WebServerHandle:
    def __init__(self):
        self._server = None
        self._thread = None

    def start(self, device: str, host: str = "127.0.0.1", port: int | None = None, sim_host: str = "127.0.0.1", sim_port: int = 5000):
        create_app, default_port = _resolve_app_factory(device)
        if port is None:
            port = default_port

        import uvicorn

        app = create_app(sim_host=sim_host, sim_port=sim_port)
        config = uvicorn.Config(app, host=host, port=port, reload=False, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

        for _ in range(50):
            if getattr(self._server, "started", False):
                break
            time.sleep(0.1)

        return f"http://{host}:{port}"

    def stop(self):
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
