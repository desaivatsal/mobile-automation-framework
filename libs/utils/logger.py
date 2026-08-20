"""Framework-level Python logging.

Robot Framework already produces ``log.html``. This module adds a plain-text
rotating log on disk, which is what you actually want when a CI job dies before
Robot can write its report, or when you need to grep across many runs.

Anything logged through :func:`get_logger` lands in *both* the file and the
Robot log (via the ``robot.api.logger`` bridge) when running under Robot.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONFIGURED = False
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-28s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class _RobotLogBridge(logging.Handler):
    """Forwards Python log records into the Robot Framework log, when present."""

    _LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from robot.api import logger as robot_logger
            from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

            try:
                BuiltIn().get_variable_value("${SUITE NAME}")
            except RobotNotRunningError:
                return
            level = self._LEVEL_MAP.get(record.levelno, "INFO")
            robot_logger.write(self.format(record), level)
        except Exception:  # noqa: BLE001 - logging must never break a test run
            pass


def configure_logging(
    log_dir: str | os.PathLike[str] = "results/logs",
    file_name: str = "execution.log",
    level: str = "INFO",
    console_level: str = "INFO",
) -> Path:
    """Configure root logging once per process. Returns the log file path."""
    global _CONFIGURED  # noqa: PLW0603

    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / file_name

    if _CONFIGURED:
        return log_file

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(_normalise(level))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(_normalise(console_level))

    bridge = _RobotLogBridge()
    bridge.setFormatter(logging.Formatter("%(message)s"))
    bridge.setLevel(_normalise(level))

    root = logging.getLogger("framework")
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.addHandler(bridge)
    root.propagate = False

    _CONFIGURED = True
    return log_file


def _normalise(level: str) -> int:
    mapping = {"TRACE": logging.DEBUG, "WARN": logging.WARNING}
    name = str(level).upper()
    return mapping.get(name, getattr(logging, name, logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger. Safe to call before :func:`configure_logging`."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(f"framework.{name}")
