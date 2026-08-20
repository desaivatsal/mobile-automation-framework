"""Layered configuration loading.

Precedence, lowest to highest:

1. ``config/default.yaml``
2. ``config/platforms/<platform>.yaml``
3. ``config/environments/<env>.yaml``
4. Process environment variables (and ``.env`` for local runs)
5. Explicit overrides passed by the caller (i.e. Robot ``--variable``)

Nothing in this module talks to Appium or Robot, so it is unit-testable in
isolation - see ``tests/unit/test_config_loader.py``.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

VALID_ENVIRONMENTS = ("dev", "qa", "staging", "prod")
VALID_PLATFORMS = ("android", "ios")
VALID_TARGETS = ("sauce_vdc", "sauce_rdc", "local")

# Environment variable -> dotted config path. Keeps the mapping explicit rather
# than magically slurping every SAUCE_* variable into the config tree.
ENV_OVERRIDES: dict[str, str] = {
    "TEST_ENV": "execution.env",
    "TEST_TARGET": "execution.target",
    "PLATFORM": "execution.platform",
    "APP_KEY": "execution.app_key",
    "BUILD_NAME": "execution.build_name",
    "SAUCE_REGION": "sauce.region",
    "SAUCE_APPIUM_VERSION": "sauce.appium_version",
    "LOG_LEVEL": "logging.level",
    "SCREENSHOT_POLICY": "reporting.screenshot_policy",
    "WEB_BASE_URL": "web.base_url",
    "API_BASE_URL": "api.base_url",
    "APPIUM_HOST": "local.host",
    "APPIUM_PORT": "local.port",
}


class ConfigError(RuntimeError):
    """Raised when configuration is missing or contradictory."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file must contain a mapping: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _set_dotted(tree: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    node = tree
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            raise ConfigError(f"Cannot set '{dotted}': '{part}' is not a mapping")
    node[parts[-1]] = value


def _coerce(value: str) -> Any:
    """Turn a string env var into bool/int/float where it obviously is one."""
    lowered = value.strip().lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _load_dotenv() -> None:
    """Load ``.env`` for local runs. In CI the values come from real env vars."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dotenv is a hard dependency
        return
    # override=False so real environment variables always beat the file.
    load_dotenv(env_file, override=False)


def load_config(
    env: str | None = None,
    platform: str | None = None,
    target: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the effective configuration tree."""
    _load_dotenv()

    env = (env or os.getenv("TEST_ENV") or "qa").lower()
    platform = (platform or os.getenv("PLATFORM") or "android").lower()
    target = (target or os.getenv("TEST_TARGET") or "sauce_vdc").lower()

    if env not in VALID_ENVIRONMENTS:
        raise ConfigError(f"Unknown environment '{env}'. Expected one of {VALID_ENVIRONMENTS}")
    if platform not in VALID_PLATFORMS:
        raise ConfigError(f"Unknown platform '{platform}'. Expected one of {VALID_PLATFORMS}")
    if target not in VALID_TARGETS:
        raise ConfigError(f"Unknown target '{target}'. Expected one of {VALID_TARGETS}")

    config = _read_yaml(CONFIG_DIR / "default.yaml")
    config = deep_merge(
        config, {"platform": _read_yaml(CONFIG_DIR / "platforms" / f"{platform}.yaml")}
    )
    config = deep_merge(config, _read_yaml(CONFIG_DIR / "environments" / f"{env}.yaml"))

    # These three are decided by the caller, not by a YAML file.
    _set_dotted(config, "execution.env", env)
    _set_dotted(config, "execution.platform", platform)
    _set_dotted(config, "execution.target", target)

    for var, dotted in ENV_OVERRIDES.items():
        raw = os.getenv(var)
        if raw not in (None, ""):
            _set_dotted(config, dotted, _coerce(raw))

    # Re-assert, because ENV_OVERRIDES could have clobbered the explicit args.
    _set_dotted(config, "execution.env", env)
    _set_dotted(config, "execution.platform", platform)
    _set_dotted(config, "execution.target", target)

    config = deep_merge(config, overrides or {})
    config["apps"] = _read_yaml(CONFIG_DIR / "apps.yaml")
    config["project_root"] = str(PROJECT_ROOT)
    return config


def resolve_app(config: dict[str, Any]) -> dict[str, Any]:
    """Return the app definition for the active ``app_key`` + ``platform``."""
    app_key = config["execution"]["app_key"]
    platform = config["execution"]["platform"]
    apps = config.get("apps", {})

    if app_key not in apps:
        raise ConfigError(
            f"App '{app_key}' is not defined in config/apps.yaml. "
            f"Known apps: {sorted(k for k in apps if isinstance(apps[k], dict))}"
        )
    definition = apps[app_key].get(platform)
    if not definition:
        raise ConfigError(f"App '{app_key}' has no '{platform}' definition in config/apps.yaml")

    storage = str(definition.get("storage", ""))
    if not storage or "REPLACE_ME" in storage:
        raise ConfigError(
            f"App '{app_key}' ({platform}) has no valid Sauce storage reference. "
            "Run `python scripts/list_sauce_apps.py` to see what is uploaded, "
            "then update config/apps.yaml."
        )
    return definition


def load_test_data(config: dict[str, Any]) -> dict[str, Any]:
    """Load the environment's test-data file, if one is configured."""
    relative = config.get("test_data_file")
    if not relative:
        return {}
    path = PROJECT_ROOT / relative
    if not path.exists():
        return {}
    return _read_yaml(path)


def sauce_credentials() -> tuple[str, str]:
    """Return ``(username, access_key)`` or raise a clear, actionable error."""
    _load_dotenv()
    username = os.getenv("SAUCE_USERNAME", "").strip()
    access_key = os.getenv("SAUCE_ACCESS_KEY", "").strip()
    if not username or not access_key:
        raise ConfigError(
            "SAUCE_USERNAME and SAUCE_ACCESS_KEY must be set. Locally: copy .env.example "
            "to .env and fill them in. In CI: add them as GitHub Actions secrets. "
            "Note SAUCE_USERNAME is the username from https://app.saucelabs.com/user-settings, "
            "not your login email."
        )
    return username, access_key
