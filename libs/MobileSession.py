"""Robot Framework library that owns the Appium session lifecycle.

Why this exists instead of calling ``Open Application`` directly from Robot:

* capabilities are assembled in Python from layered config, so a test never
  hardcodes a device, an app or a Sauce option;
* session creation is retried - Sauce intermittently fails to allocate a
  device, and a flaky ``SessionNotCreatedException`` should not fail a build;
* the Sauce job is named after the running test and its pass/fail status is
  pushed back to the dashboard, which Appium itself will not do;
* the access key never reaches the Robot log.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

# Allow `Library  ../../libs/MobileSession.py` (import by path) to work without
# the project root already being on PYTHONPATH.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from robot.api import logger as robot_logger
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

from libs.capabilities import build_capabilities, redact, remote_url
from libs.config_loader import load_config
from libs.utils.logger import get_logger

LOG = get_logger("session")


class MobileSession:
    """Appium session management for Sauce Labs and local Appium servers."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._config: dict[str, Any] | None = None
        self._session_id: str | None = None
        self._job_reported = False

    # ------------------------------------------------------------- internals
    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            self._config = self._config_from_robot() or load_config()
        return self._config

    @staticmethod
    def _config_from_robot() -> dict[str, Any] | None:
        try:
            return BuiltIn().get_variable_value("${CONFIG}")
        except RobotNotRunningError:
            return None

    @staticmethod
    def _appium_library() -> Any:
        return BuiltIn().get_library_instance("AppiumLibrary")

    @staticmethod
    def _current_test_name() -> str:
        try:
            return BuiltIn().get_variable_value("${TEST NAME}") or "Suite Setup"
        except RobotNotRunningError:
            return "Suite Setup"

    @property
    def _is_real_device(self) -> bool:
        return self.config["execution"]["target"] == "sauce_rdc"

    # -------------------------------------------------------------- keywords
    @keyword("Open Test Application")
    def open_test_application(self, alias: str | None = None) -> str:
        """Start an Appium session for the configured app, platform and target.

        Retries session creation according to ``retry.session_start_attempts``.
        """
        config = self.config
        caps = build_capabilities(config, test_name=self._current_test_name())
        url = remote_url(config)

        robot_logger.info(f"Appium endpoint: {url}")
        robot_logger.info(f"Capabilities: {redact(caps)}")

        attempts = int(config["retry"]["session_start_attempts"])
        backoff = float(config["retry"]["session_start_backoff_seconds"])
        library = self._appium_library()

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                library.open_application(url, alias=alias, **caps)
                break
            except Exception as exc:  # noqa: BLE001 - any driver failure is retryable
                last_error = exc
                LOG.warning("Session start attempt %s/%s failed: %s", attempt, attempts, exc)
                if attempt == attempts:
                    raise AssertionError(
                        f"Could not start an Appium session after {attempts} attempts. "
                        f"Last error: {exc}"
                    ) from last_error
                time.sleep(backoff * attempt)

        self._session_id = library.get_appium_sessionId()
        self._job_reported = False
        BuiltIn().set_global_variable("${SAUCE_SESSION_ID}", self._session_id)

        if config["execution"]["target"] != "local":
            link = self.get_sauce_job_link()
            BuiltIn().set_global_variable("${SAUCE_JOB_URL}", link)
            if config["reporting"]["embed_sauce_links"]:
                robot_logger.info(
                    f'Sauce job: <a href="{link}" target="_blank">{link}</a>', html=True
                )

        library.set_appium_timeout(f"{config['timeouts']['element_wait']}s")
        return self._session_id

    @keyword("Close Test Application")
    def close_test_application(self) -> None:
        """Report the result to Sauce, then close the session.

        Safe to call when no session is open, so it can live in an
        unconditional suite teardown.
        """
        try:
            self.report_sauce_status()
        finally:
            try:
                self._appium_library().close_application()
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Closing the Appium session failed (ignored): %s", exc)
            self._session_id = None

    @keyword("Report Sauce Status")
    def report_sauce_status(self, passed: bool | None = None) -> None:
        """Push pass/fail to the Sauce dashboard. No-op locally or if already sent."""
        config = self.config
        if config["execution"]["target"] == "local" or not self._session_id or self._job_reported:
            return

        if passed is None:
            try:
                status = BuiltIn().get_variable_value("${TEST STATUS}")
                # ${TEST STATUS} is unset outside a test - fall back to the suite.
                if status is None:
                    status = BuiltIn().get_variable_value("${SUITE STATUS}") or "PASS"
            except RobotNotRunningError:
                status = "PASS"
            passed = str(status).upper() == "PASS"

        from libs.sauce_client import SauceClient

        try:
            SauceClient(config["sauce"]["region"]).set_job_status(
                self._session_id, bool(passed), real_device=self._is_real_device
            )
            self._job_reported = True
        except Exception as exc:  # noqa: BLE001 - reporting must never fail a run
            LOG.warning("Could not report Sauce job status: %s", exc)

    @keyword("Get Sauce Job Link")
    def get_sauce_job_link(self) -> str:
        """Dashboard URL for the current Sauce job."""
        if not self._session_id:
            return ""
        region = self.config["sauce"]["region"]
        return f"https://app.{region}.saucelabs.com/tests/{self._session_id}"

    @keyword("Get Active Configuration")
    def get_active_configuration(self) -> dict[str, Any]:
        """Return the resolved configuration tree (for debugging and assertions)."""
        return self.config
