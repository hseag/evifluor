# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import json
import urllib.error
import urllib.parse
import urllib.request


class RestApiError(RuntimeError):
    """Raised when a REST request fails or returns a non-success status."""


class RestClient:
    """HTTP client for the eviFluor REST API."""

    def __init__(self, base_url="http://127.0.0.1:8000", serial_number=None):
        self.base_url = base_url.rstrip("/")
        self.serial_number = serial_number

    def _device_path(self, suffix):
        if self.serial_number:
            device_id = urllib.parse.quote(self.serial_number)
            return f"{self.base_url}/api/v1/devices/{device_id}/{suffix}"
        return f"{self.base_url}/api/v1/device/{suffix}"

    def _run_path(self, run_id, suffix=""):
        encoded = urllib.parse.quote(run_id)
        if suffix:
            return f"{self.base_url}/api/v1/runs/{encoded}/{suffix}"
        return f"{self.base_url}/api/v1/runs/{encoded}"

    def _request_json(self, method, url, payload=None):
        data = None
        headers = {}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RestApiError(f"HTTP {exc.code} for {url}\n{body}") from exc
        except urllib.error.URLError as exc:
            raise RestApiError(f"Request failed for {url}: {exc}") from exc

    def _request_text(self, method, url, payload=None):
        data = None
        headers = {}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RestApiError(f"HTTP {exc.code} for {url}\n{body}") from exc
        except urllib.error.URLError as exc:
            raise RestApiError(f"Request failed for {url}: {exc}") from exc

    def health(self):
        return self._request_json("GET", f"{self.base_url}/api/v1/health")

    def version(self):
        return self._request_json("GET", f"{self.base_url}/api/v1/version")

    def list_devices(self):
        return self._request_json("GET", f"{self.base_url}/api/v1/devices")

    def info(self):
        return self._request_json("GET", self._device_path("info"))

    def selftest(self):
        return self._request_json("POST", self._device_path("selftest"))

    def checkempty(self):
        return self._request_json("GET", self._device_path("checkempty"))

    def status(self):
        """Return the service-side device status (`idle`, `busy`, or `error`)."""
        return self._request_json("GET", self._device_path("status"))

    def run_init(self, nr_of_std_low, nr_of_std_high, concentration, no_air=False, kit="Default", settling_time=None):
        payload = {
            "nr_of_std_low": nr_of_std_low,
            "nr_of_std_high": nr_of_std_high,
            "concentration": concentration,
            "no_air": no_air,
            "kit": kit,
            "settling_time": settling_time,
        }
        if self.serial_number:
            payload["device_id"] = self.serial_number
        return self._request_json("POST", f"{self.base_url}/api/v1/runs", payload)

    def run_get(self, run_id):
        return self._request_json("GET", self._run_path(run_id))

    def run_measure(self, run_id, comment=None):
        return self._request_json("POST", self._run_path(run_id, "measure"), {"comment": comment})

    def run_export_csv(self, run_id):
        return self._request_text("POST", self._run_path(run_id, "export/csv"), {})

    def run_data(self, run_id):
        return self._request_json("GET", self._run_path(run_id, "data"))
