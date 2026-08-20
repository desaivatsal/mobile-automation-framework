"""Thin Sauce Labs REST client.

Covers only what the framework needs:
  * marking a job passed/failed (Sauce cannot infer this from Appium alone)
  * listing / uploading app-storage binaries

Every call is best-effort where it is not on the critical path: a reporting
call must never turn a green run red.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from libs.capabilities import sauce_api_url
from libs.config_loader import sauce_credentials
from libs.utils.logger import get_logger

LOG = get_logger("sauce")
DEFAULT_TIMEOUT = 30


class SauceClient:
    def __init__(self, region: str | None = None) -> None:
        self.region = region or os.getenv("SAUCE_REGION", "us-west-1")
        self.username, self._access_key = sauce_credentials()
        self.base_url = sauce_api_url(self.region)
        self._auth = (self.username, self._access_key)

    # ------------------------------------------------------------------ jobs
    def job_url(self, session_id: str, real_device: bool = False) -> str:
        """Public dashboard URL for a job."""
        kind = "tests" if not real_device else "tests"
        return f"https://app.{self.region}.saucelabs.com/{kind}/{session_id}"

    def set_job_status(self, session_id: str, passed: bool, real_device: bool = False) -> bool:
        """Mark a Sauce job passed/failed. Returns True on success."""
        if real_device:
            url = f"{self.base_url}/v1/rdc/jobs/{session_id}"
            payload: dict[str, Any] = {"passed": passed}
            method = requests.put
        else:
            url = f"{self.base_url}/rest/v1/{self.username}/jobs/{session_id}"
            payload = {"passed": passed}
            method = requests.put

        try:
            response = method(url, json=payload, auth=self._auth, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            LOG.info("Sauce job %s marked %s", session_id, "passed" if passed else "failed")
            return True
        except requests.RequestException as exc:
            # Never fail the test because the dashboard update failed.
            LOG.warning("Could not update Sauce job %s status: %s", session_id, exc)
            return False

    # --------------------------------------------------------------- storage
    def list_apps(self, per_page: int = 100) -> list[dict[str, Any]]:
        """Return the app-storage files visible to this account."""
        url = f"{self.base_url}/v1/storage/files"
        response = requests.get(
            url, params={"per_page": per_page}, auth=self._auth, timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def upload_app(self, file_path: str | Path, description: str = "") -> dict[str, Any]:
        """Upload an .apk/.ipa/.zip to Sauce app storage and return its metadata."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"App binary not found: {path}")

        url = f"{self.base_url}/v1/storage/upload"
        with path.open("rb") as handle:
            response = requests.post(
                url,
                files={"payload": (path.name, handle)},
                data={"name": path.name, "description": description},
                auth=self._auth,
                timeout=600,
            )
        response.raise_for_status()
        item = response.json().get("item", {})
        LOG.info("Uploaded %s -> storage id %s", path.name, item.get("id"))
        return item
