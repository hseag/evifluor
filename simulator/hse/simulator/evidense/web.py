# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import argparse
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from hse.simulator.protocol import send_command


def _send_control(command: str, host: str, port: int) -> list[str]:
    return send_command(f"! {command}", host, port)


def _read_checkempty(host: str, port: int) -> bool:
    parts = send_command("X", host, port)
    return int(parts[1]) == 1


def _write_checkempty(value: bool, host: str, port: int) -> bool:
    _send_control(f"CHECKEMPTY {1 if value else 0}", host, port)
    return _read_checkempty(host, port)


def _reset_simulator(host: str, port: int) -> bool:
    _send_control("RESET", host, port)
    return _read_checkempty(host, port)


def _write_zero(value: bool, host: str, port: int) -> bool:
    _send_control(f"ZERO {1 if value else 0}", host, port)
    return value


def _load_data(path: str, host: str, port: int) -> bool:
    _send_control(f'LOAD "{path}"', host, port)
    return _read_checkempty(host, port)


def _store_uploaded_measurement(name: str, content: str) -> str:
    suffix = Path(name).suffix or ".json"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=suffix, prefix="evidense-load-", delete=False) as handle:
        handle.write(content)
        return handle.name


def create_app(sim_host: str = "127.0.0.1", sim_port: int = 5000) -> FastAPI:
    app = FastAPI(
        title="eviDense Simulator Demo",
        version="1.0",
        description="Web UI for selected eviDense simulator control commands.",
    )

    @app.get("/", response_class=HTMLResponse)
    def index():
        return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>eviDense Simulator Demo</title>
  <style>
    :root {
      --bg: #edf2ef;
      --panel: #ffffff;
      --panel-soft: #f5f8f6;
      --ink: #20303a;
      --muted: #5d6c73;
      --accent: #226f86;
      --accent-dark: #18586b;
      --accent-soft: #d8ecf2;
      --warn: #9c5f16;
      --warn-soft: #f5e6d2;
      --ok: #2f7d67;
      --border: #d6e0e4;
      --shadow: rgba(23, 37, 44, 0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Aptos", "Segoe UI", Tahoma, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(34, 111, 134, 0.18) 0, transparent 30%),
        linear-gradient(135deg, #f6f9f8, var(--bg) 48%, #e7efef);
      display: grid;
      place-items: center;
      padding: 24px;
    }
    main {
      width: min(760px, 100%);
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 24px 60px var(--shadow);
      position: relative;
      overflow: hidden;
    }
    main::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 8px;
      background: linear-gradient(90deg, var(--accent-dark), var(--accent));
    }
    h1 {
      margin: 0 0 8px;
      font-size: 2rem;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }
    p {
      margin: 0;
      color: var(--muted);
    }
    .status {
      margin-top: 24px;
      padding: 16px 18px;
      border-radius: 16px;
      background: var(--panel-soft);
      border: 1px solid var(--border);
    }
    .state {
      margin-top: 10px;
      font-size: 1.4rem;
      font-weight: 700;
    }
    .state[data-empty="true"] { color: var(--ok); }
    .state[data-empty="false"] { color: var(--accent); }
    .actions {
      margin-top: 22px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    button {
      border: 1px solid transparent;
      border-radius: 14px;
      padding: 14px 16px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease, background-color 120ms ease, border-color 120ms ease;
      background: white;
      color: var(--ink);
    }
    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.6; cursor: wait; transform: none; }
    .btn-empty { background: var(--ok); color: white; }
    .btn-filled { background: var(--accent); color: white; }
    #btn-reset,
    #btn-load,
    #btn-upload-load {
      border-color: var(--accent-soft);
      background: #fbfdfe;
    }
    #btn-reset:hover,
    #btn-load:hover,
    #btn-upload-load:hover {
      background: var(--accent-soft);
    }
    .footer {
      margin-top: 16px;
      font-size: 0.9rem;
      color: var(--muted);
    }
    .toggle-row,
    .load-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 12px;
      flex-wrap: wrap;
    }
    input[type="text"] {
      flex: 1;
      min-width: 0;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      font: inherit;
      color: var(--ink);
      background: white;
    }
    input[type="text"]:focus {
      outline: 2px solid rgba(34, 111, 134, 0.16);
      border-color: var(--accent);
    }
    input[type="checkbox"] {
      width: 20px;
      height: 20px;
      accent-color: var(--warn);
    }
    input[type="file"] {
      flex: 1 1 280px;
      min-width: 0;
      max-width: 100%;
      font: inherit;
      overflow: hidden;
    }
    code {
      background: #eef3f5;
      padding: 2px 6px;
      border-radius: 999px;
    }
  </style>
</head>
<body>
  <main>
    <h1>eviDense Simulator</h1>
    <p>Control UI for selected simulator commands on the running <code>eviDense</code> instance.</p>
    <section class="status">
      <div>Current cuvette-guide state</div>
      <div id="state" class="state" data-empty="unknown">Loading...</div>
    </section>
    <section class="actions">
      <button id="btn-empty" class="btn-empty" type="button">Set Empty</button>
      <button id="btn-filled" class="btn-filled" type="button">Set Filled</button>
      <button id="btn-reset" type="button">Reset Simulator</button>
    </section>
    <section class="status">
      <div>Zero-value mode</div>
      <div class="toggle-row">
        <label for="zero-mode">ZERO</label>
        <input id="zero-mode" type="checkbox">
      </div>
    </section>
    <section class="status">
      <div>Load measurement data</div>
      <div class="load-row">
        <input id="load-path" type="text" placeholder="Path to JSON measurement file">
        <button id="btn-load" type="button">Load File</button>
      </div>
      <div class="load-row">
        <input id="load-file" type="file" accept=".json,application/json">
        <button id="btn-upload-load" type="button">Open And Load</button>
      </div>
    </section>
    <div id="message" class="footer" aria-live="polite"></div>
    <div class="footer">Simulator target: <code>""" + sim_host + ":" + str(sim_port) + """</code></div>
  </main>
  <script>
    const stateEl = document.getElementById("state");
    const messageEl = document.getElementById("message");
    const zeroModeEl = document.getElementById("zero-mode");
    const loadPathEl = document.getElementById("load-path");
    const loadFileEl = document.getElementById("load-file");
    const controls = [
      document.getElementById("btn-empty"),
      document.getElementById("btn-filled"),
      document.getElementById("btn-reset"),
      zeroModeEl,
      document.getElementById("btn-load"),
      document.getElementById("btn-upload-load"),
      loadPathEl,
      loadFileEl,
    ];
    function setBusy(busy) { controls.forEach((control) => control.disabled = busy); }
    function setMessage(text, isError = false) {
      messageEl.textContent = text;
      messageEl.style.color = isError ? "#b42318" : "";
    }
    function renderState(empty) {
      stateEl.dataset.empty = String(empty);
      stateEl.textContent = empty ? "EMPTY" : "FILLED";
    }
    async function refresh() {
      setBusy(true);
      try {
        const response = await fetch("/api/checkempty");
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to read simulator state"); }
        renderState(payload.empty);
        setMessage("");
      } catch (error) {
        stateEl.dataset.empty = "unknown";
        stateEl.textContent = error.message;
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    async function update(empty) {
      setBusy(true);
      try {
        const response = await fetch("/api/checkempty", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ empty }),
        });
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to update simulator state"); }
        renderState(payload.empty);
        setMessage("CHECKEMPTY updated.");
      } catch (error) {
        stateEl.dataset.empty = "unknown";
        stateEl.textContent = error.message;
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    async function resetSimulator() {
      setBusy(true);
      try {
        const response = await fetch("/api/reset", { method: "POST" });
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to reset simulator"); }
        renderState(payload.empty);
        zeroModeEl.checked = false;
        setMessage("Simulator reset. ZERO mode is off again.");
      } catch (error) {
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    async function setZero(enabled) {
      setBusy(true);
      try {
        const response = await fetch("/api/zero", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        });
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to update ZERO mode"); }
        zeroModeEl.checked = payload.enabled;
        setMessage(`ZERO mode ${payload.enabled ? "enabled" : "disabled"}.`);
      } catch (error) {
        zeroModeEl.checked = !enabled;
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    async function loadData() {
      const path = loadPathEl.value.trim();
      if (!path) {
        setMessage("Please enter a measurement file path.", true);
        return;
      }
      setBusy(true);
      try {
        const response = await fetch("/api/load", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path }),
        });
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to load measurement file"); }
        renderState(payload.empty);
        setMessage(`Loaded ${payload.path}.`);
      } catch (error) {
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    async function loadSelectedFile() {
      const file = loadFileEl.files[0];
      if (!file) {
        setMessage("Please choose a JSON measurement file.", true);
        return;
      }
      setBusy(true);
      try {
        const content = await file.text();
        const response = await fetch("/api/load-upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: file.name, content }),
        });
        const payload = await response.json();
        if (!response.ok) { throw new Error(payload.detail || "Unable to upload and load measurement file"); }
        renderState(payload.empty);
        loadPathEl.value = payload.path;
        setMessage(`Loaded ${payload.name}.`);
      } catch (error) {
        setMessage(error.message, true);
      } finally {
        setBusy(false);
      }
    }
    document.getElementById("btn-empty").addEventListener("click", () => update(true));
    document.getElementById("btn-filled").addEventListener("click", () => update(false));
    document.getElementById("btn-reset").addEventListener("click", resetSimulator);
    zeroModeEl.addEventListener("change", () => setZero(zeroModeEl.checked));
    document.getElementById("btn-load").addEventListener("click", loadData);
    document.getElementById("btn-upload-load").addEventListener("click", loadSelectedFile);
    refresh();
  </script>
</body>
</html>"""

    @app.get("/api/checkempty")
    def get_checkempty():
        try:
            return {"empty": _read_checkempty(sim_host, sim_port)}
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/checkempty")
    def set_checkempty(payload: dict):
        if "empty" not in payload or not isinstance(payload["empty"], bool):
            raise HTTPException(status_code=400, detail="JSON body must contain boolean field 'empty'")
        try:
            return {"empty": _write_checkempty(payload["empty"], sim_host, sim_port)}
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/reset")
    def reset():
        try:
            return {"empty": _reset_simulator(sim_host, sim_port)}
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/zero")
    def set_zero(payload: dict):
        if "enabled" not in payload or not isinstance(payload["enabled"], bool):
            raise HTTPException(status_code=400, detail="JSON body must contain boolean field 'enabled'")
        try:
            return {"enabled": _write_zero(payload["enabled"], sim_host, sim_port)}
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/load")
    def load(payload: dict):
        path = payload.get("path")
        if not isinstance(path, str) or not path.strip():
            raise HTTPException(status_code=400, detail="JSON body must contain non-empty string field 'path'")
        try:
            return {"path": path, "empty": _load_data(path.strip(), sim_host, sim_port)}
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/load-upload")
    def load_upload(payload: dict):
        name = payload.get("name")
        content = payload.get("content")
        if not isinstance(name, str) or not name.strip():
            raise HTTPException(status_code=400, detail="JSON body must contain non-empty string field 'name'")
        if not isinstance(content, str) or not content.strip():
            raise HTTPException(status_code=400, detail="JSON body must contain non-empty string field 'content'")
        try:
            stored_path = _store_uploaded_measurement(name.strip(), content)
            return {
                "name": name.strip(),
                "path": stored_path,
                "empty": _load_data(stored_path, sim_host, sim_port),
            }
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"Simulator not reachable at {sim_host}:{sim_port}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m hse.simulator.evidense.web",
        description="Start a minimal web UI for the eviDense simulator.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for the web UI")
    parser.add_argument("--port", type=int, default=8011, help="Bind port for the web UI")
    parser.add_argument("--sim-host", default="127.0.0.1", help="Host of the running simulator")
    parser.add_argument("--sim-port", type=int, default=5000, help="Port of the running simulator")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    import uvicorn

    uvicorn.run(create_app(sim_host=args.sim_host, sim_port=args.sim_port), host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
