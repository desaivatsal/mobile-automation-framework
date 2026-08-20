"""W3C capability construction for Sauce Labs and local Appium.

Kept separate from session management so the payload can be asserted in unit
tests without ever opening a driver.
"""

from __future__ import annotations

import os
from typing import Any

from libs.config_loader import ConfigError, resolve_app, sauce_credentials

SAUCE_REGIONS = ("us-west-1", "eu-central-1", "us-east-4", "apac-southeast-1")

# Capabilities that must NOT be sent to Sauce real devices - they are
# emulator/simulator concepts and cause the job to be rejected or ignored.
RDC_UNSUPPORTED_CAPS = frozenset({"avd", "systemPort", "chromedriverExecutable"})
RDC_UNSUPPORTED_SAUCE_OPTS = frozenset({"idleTimeout"})


def sauce_hub_url(region: str) -> str:
    """Appium endpoint for a Sauce data centre. Serves both VDC and RDC."""
    if region not in SAUCE_REGIONS:
        raise ConfigError(f"Unknown Sauce region '{region}'. Expected one of {SAUCE_REGIONS}")
    return f"https://ondemand.{region}.saucelabs.com:443/wd/hub"


def sauce_api_url(region: str) -> str:
    """REST API base for a Sauce data centre."""
    if region not in SAUCE_REGIONS:
        raise ConfigError(f"Unknown Sauce region '{region}'. Expected one of {SAUCE_REGIONS}")
    return f"https://api.{region}.saucelabs.com"


def _drop(mapping: dict[str, Any], blocked: frozenset) -> dict[str, Any]:
    return {k: v for k, v in mapping.items() if k not in blocked and v not in (None, "")}


def build_capabilities(
    config: dict[str, Any], test_name: str = "Robot Framework Suite"
) -> dict[str, Any]:
    """Build the flat capability mapping handed to ``Open Application``.

    Keys containing ``:`` are passed through untouched; everything else is
    prefixed with ``appium:`` by the Appium client. That is why ``platformName``
    stays bare and ``sauce:options`` survives as a vendor block.
    """
    execution = config["execution"]
    platform_cfg = config["platform"]
    target = execution["target"]
    timeouts = config["timeouts"]

    targets = platform_cfg.get("targets", {})
    if target not in targets:
        raise ConfigError(
            f"Target '{target}' is not configured for platform "
            f"'{execution['platform']}' in config/platforms/{execution['platform']}.yaml"
        )
    target_cfg = targets[target] or {}
    app = resolve_app(config)

    caps: dict[str, Any] = {
        "platformName": platform_cfg["platform_name"],
        "automationName": platform_cfg["automation_name"],
    }
    caps.update(dict(target_cfg.get("capabilities") or {}))

    if target == "local":
        # Locally the app is a path on disk, not a Sauce storage reference.
        local_app = os.getenv("LOCAL_APP_PATH", "").strip()
        if not local_app:
            raise ConfigError(
                "TEST_TARGET=local requires LOCAL_APP_PATH to point at an .apk/.app on disk."
            )
        caps["app"] = local_app
    else:
        caps["app"] = app["storage"]

    # Android-only hints that make the driver attach to the right activity.
    if execution["platform"] == "android":
        if app.get("app_package"):
            caps["appPackage"] = app["app_package"]
        if app.get("app_activity"):
            caps["appActivity"] = app["app_activity"]
    elif app.get("bundle_id"):
        caps["bundleId"] = app["bundle_id"]

    if target == "local":
        return _drop(caps, frozenset())

    username, access_key = sauce_credentials()
    sauce_cfg = config["sauce"]

    sauce_options: dict[str, Any] = {
        "username": username,
        "accessKey": access_key,
        "name": test_name,
        "build": _build_label(config),
        "tags": list(sauce_cfg.get("tags") or [])
        + [execution["env"], execution["platform"], target],
        "appiumVersion": str(sauce_cfg.get("appium_version", "2")),
        "maxDuration": timeouts["max_session_duration"],
        "commandTimeout": timeouts["command_timeout"],
        "idleTimeout": timeouts["idle_timeout"],
    }
    sauce_options.update(dict(target_cfg.get("sauce_options") or {}))

    if target == "sauce_rdc":
        caps = _drop(caps, RDC_UNSUPPORTED_CAPS)
        sauce_options = _drop(sauce_options, RDC_UNSUPPORTED_SAUCE_OPTS)
    else:
        caps = _drop(caps, frozenset())
        sauce_options = _drop(sauce_options, frozenset())

    caps["sauce:options"] = sauce_options
    return caps


def _build_label(config: dict[str, Any]) -> str:
    """Group jobs in the Sauce dashboard by CI build, falling back to local."""
    execution = config["execution"]
    run_id = os.getenv("GITHUB_RUN_ID")
    if run_id:
        repo = os.getenv("GITHUB_REPOSITORY", "local")
        return f"{repo}#{os.getenv('GITHUB_RUN_NUMBER', run_id)}-{execution['env']}"
    return f"{execution['build_name']}-{execution['env']}-{execution['platform']}"


def redact(caps: dict[str, Any]) -> dict[str, Any]:
    """Copy of the capabilities with the access key masked - safe to log."""
    import copy

    safe = copy.deepcopy(caps)
    if isinstance(safe.get("sauce:options"), dict) and "accessKey" in safe["sauce:options"]:
        safe["sauce:options"]["accessKey"] = "***redacted***"
    return safe


def remote_url(config: dict[str, Any]) -> str:
    """Appium endpoint for the active target."""
    target = config["execution"]["target"]
    if target == "local":
        host = config.get("local", {}).get("host") or os.getenv("APPIUM_HOST", "127.0.0.1")
        port = config.get("local", {}).get("port") or os.getenv("APPIUM_PORT", "4723")
        return f"http://{host}:{port}"
    return sauce_hub_url(config["sauce"]["region"])
