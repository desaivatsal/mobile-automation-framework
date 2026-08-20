"""Failure-evidence listener.

Hooks Robot's listener API v3 so evidence is captured at the moment a keyword
fails - while the driver is still alive - rather than in teardown, by which
point the app may have been reset or the session already closed.

Captured per failing test (once, not once per nested keyword):
  * PNG screenshot, embedded in log.html and written to results/screenshots/
  * XML page source, written to results/page_source/
  * the Sauce job link, so a CI failure is one click from the video

Enable with::

    robot --listener libs/listeners/EvidenceListener.py ...
    robot --listener libs/listeners/EvidenceListener.py:full ...   # every test

``screenshot_policy`` argument: ``failures_only`` (default) | ``full`` | ``none``.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Allow `--listener libs/listeners/EvidenceListener.py` (import by path).
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from robot.api import logger as robot_logger
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _slug(text: str, limit: int = 60) -> str:
    return _SAFE.sub("_", str(text)).strip("_")[:limit] or "unnamed"


class EvidenceListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, screenshot_policy: str | None = None) -> None:
        self._policy_override = screenshot_policy
        self._captured_for_test = False
        self._test_name = ""
        self._suite_name = ""
        self._counter = 0

    # ------------------------------------------------------------- internals
    @property
    def _policy(self) -> str:
        if self._policy_override:
            return self._policy_override.lower()
        env_policy = os.getenv("SCREENSHOT_POLICY")
        if env_policy:
            return env_policy.lower()
        try:
            config = BuiltIn().get_variable_value("${CONFIG}")
            if config:
                return str(config["reporting"]["screenshot_policy"]).lower()
        except (RobotNotRunningError, KeyError, TypeError):
            pass
        return "failures_only"

    @staticmethod
    def _appium():
        try:
            library = BuiltIn().get_library_instance("AppiumLibrary")
        except (RobotNotRunningError, RuntimeError):
            return None
        # No open session -> nothing to capture.
        try:
            if not library._cache.current:  # noqa: SLF001 - no public accessor exists
                return None
        except Exception:  # noqa: BLE001
            return None
        return library

    @staticmethod
    def _output_dir() -> Path:
        try:
            return Path(BuiltIn().get_variable_value("${OUTPUT DIR}") or ".")
        except RobotNotRunningError:
            return Path(".")

    def _capture(self, reason: str) -> None:
        library = self._appium()
        if library is None:
            return

        self._counter += 1
        stem = f"{_slug(self._suite_name, 30)}-{_slug(self._test_name)}-{self._counter}"

        screenshots = self._output_dir() / "screenshots"
        screenshots.mkdir(parents=True, exist_ok=True)
        try:
            library.capture_page_screenshot(f"screenshots/{stem}.png")
            robot_logger.info(f"Evidence captured ({reason}): screenshots/{stem}.png")
        except Exception as exc:  # noqa: BLE001 - evidence capture is best effort
            robot_logger.warn(f"Screenshot capture failed: {exc}")

        sources = self._output_dir() / "page_source"
        sources.mkdir(parents=True, exist_ok=True)
        try:
            (sources / f"{stem}.xml").write_text(library.get_source(), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            robot_logger.debug(f"Page source capture failed: {exc}")

    # -------------------------------------------------------- listener hooks
    def start_suite(self, data, result) -> None:  # noqa: ANN001, ARG002
        self._suite_name = data.name

    def start_test(self, data, result) -> None:  # noqa: ANN001, ARG002
        self._test_name = data.name
        self._captured_for_test = False
        self._counter = 0

    def end_keyword(self, data, result) -> None:  # noqa: ANN001, ARG002
        if self._policy == "none" or self._captured_for_test:
            return
        if result.status != "FAIL":
            return
        self._captured_for_test = True
        self._capture("keyword failed")

    def end_test(self, data, result) -> None:  # noqa: ANN001
        if self._policy == "full" and not self._captured_for_test:
            self._capture("full policy")

        if result.status == "FAIL":
            try:
                job_url = BuiltIn().get_variable_value("${SAUCE_JOB_URL}")
            except RobotNotRunningError:
                job_url = None
            if job_url:
                robot_logger.info(
                    f'Sauce video for this failure: <a href="{job_url}">{job_url}</a>',
                    html=True,
                )
                result.message = f"{result.message}\n\nSauce job: {job_url}"
