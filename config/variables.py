"""Robot Framework variable file - the single entry point for configuration.

Usage::

    robot --variablefile config/variables.py:qa:android:sauce_vdc tests/mobile

Positional arguments are ``env:platform:target``; any omitted argument falls
back to the matching environment variable, then to the default in
``config/default.yaml``.

Deliberately does NOT resolve Sauce credentials or build capabilities. Those
happen at session-open time so that ``robot --dryrun`` and Robocop can run in
CI without any secrets present.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from libs.config_loader import load_config, load_test_data  # noqa: E402
from libs.utils.logger import configure_logging  # noqa: E402


def get_variables(
    env: str | None = None,
    platform: str | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    config = load_config(env=env, platform=platform, target=target)
    execution = config["execution"]

    log_file = configure_logging(
        log_dir=PROJECT_ROOT / config["reporting"]["logs_dir"],
        file_name=config["logging"]["file_name"],
        level=config["logging"]["level"],
        console_level=config["logging"]["console_level"],
    )

    return {
        # Whole tree, for anything not surfaced individually below.
        "CONFIG": config,
        "ROOT": str(PROJECT_ROOT),
        # Execution context
        "ENV": execution["env"],
        "PLATFORM": execution["platform"],
        "TARGET": execution["target"],
        "APP_KEY": execution["app_key"],
        "BUILD_NAME": execution["build_name"],
        "IS_ANDROID": execution["platform"] == "android",
        "IS_IOS": execution["platform"] == "ios",
        "IS_REAL_DEVICE": execution["target"] == "sauce_rdc",
        # Timeouts - tests and page objects must use these, never literals
        "ELEMENT_WAIT": f"{config['timeouts']['element_wait']}s",
        "PAGE_LOAD_TIMEOUT": f"{config['timeouts']['page_load']}s",
        "APP_LAUNCH_TIMEOUT": f"{config['timeouts']['app_launch']}s",
        # Reporting
        "SCREENSHOT_POLICY": config["reporting"]["screenshot_policy"],
        "FRAMEWORK_LOG_FILE": str(log_file),
        # Placeholders filled in at runtime by MobileSession
        "SAUCE_SESSION_ID": "",
        "SAUCE_JOB_URL": "",
        # Future layers
        "WEB_BASE_URL": config["web"]["base_url"],
        "API_BASE_URL": config["api"]["base_url"],
        # Environment-specific test data
        "TEST_DATA": load_test_data(config),
    }
