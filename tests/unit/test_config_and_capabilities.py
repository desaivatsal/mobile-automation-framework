"""Unit tests for the configuration and capability layers.

These run in seconds with no device, no Appium and no Sauce account, and they
are what stops a bad capability payload reaching a paid cloud session. Run with:

    pytest tests/unit -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.capabilities import build_capabilities, redact, remote_url, sauce_hub_url  # noqa: E402
from libs.config_loader import ConfigError, deep_merge, load_config, resolve_app  # noqa: E402


@pytest.fixture(autouse=True)
def _sauce_env(monkeypatch):
    monkeypatch.setenv("SAUCE_USERNAME", "unit-test-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "unit-test-key")
    # Stop a developer's local .env from changing test outcomes.
    for var in ("TEST_ENV", "PLATFORM", "TEST_TARGET", "APP_KEY", "BUILD_NAME", "GITHUB_RUN_ID"):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------------- config
def test_deep_merge_does_not_mutate_the_base():
    base = {"a": {"b": 1, "c": 2}}
    merged = deep_merge(base, {"a": {"c": 3}})
    assert merged == {"a": {"b": 1, "c": 3}}
    assert base == {"a": {"b": 1, "c": 2}}


def test_environment_overrides_default():
    default_cfg = load_config(env="qa", platform="android", target="sauce_vdc")
    dev_cfg = load_config(env="dev", platform="android", target="sauce_vdc")
    assert default_cfg["logging"]["level"] == "INFO"
    assert dev_cfg["logging"]["level"] == "DEBUG"
    assert dev_cfg["reporting"]["screenshot_policy"] == "full"


def test_explicit_arguments_beat_environment_variables(monkeypatch):
    monkeypatch.setenv("PLATFORM", "ios")
    config = load_config(env="qa", platform="android", target="sauce_vdc")
    assert config["execution"]["platform"] == "android"


@pytest.mark.parametrize(
    ("env", "platform", "target"),
    [("nope", "android", "sauce_vdc"), ("qa", "windows", "sauce_vdc"), ("qa", "android", "farm")],
)
def test_invalid_selectors_are_rejected(env, platform, target):
    with pytest.raises(ConfigError):
        load_config(env=env, platform=platform, target=target)


def test_unconfigured_app_raises_actionable_error():
    config = load_config(env="qa", platform="android", target="sauce_vdc")
    config["execution"]["app_key"] = "element_app"
    with pytest.raises(ConfigError, match="list_sauce_apps"):
        resolve_app(config)


# --------------------------------------------------------------- capabilities
def test_android_vdc_capability_payload():
    config = load_config(env="qa", platform="android", target="sauce_vdc")
    caps = build_capabilities(config, test_name="Valid User Can Log In")

    assert caps["platformName"] == "Android"
    assert caps["automationName"] == "UiAutomator2"
    assert caps["app"].startswith("storage:filename=")
    assert caps["appPackage"] == "com.swaglabsmobileapp"

    sauce = caps["sauce:options"]
    assert sauce["username"] == "unit-test-user"
    assert sauce["accessKey"] == "unit-test-key"
    assert sauce["name"] == "Valid User Can Log In"
    assert "qa" in sauce["tags"] and "android" in sauce["tags"]


def test_ios_capability_payload_uses_xcuitest():
    config = load_config(env="qa", platform="ios", target="sauce_vdc")
    caps = build_capabilities(config)
    assert caps["platformName"] == "iOS"
    assert caps["automationName"] == "XCUITest"
    assert caps["bundleId"] == "com.saucelabs.mydemoapp.rn"
    assert "appPackage" not in caps


def test_real_device_target_strips_emulator_only_options():
    config = load_config(env="qa", platform="android", target="sauce_rdc")
    caps = build_capabilities(config)
    assert "idleTimeout" not in caps["sauce:options"]
    assert "avd" not in caps


def test_build_label_uses_github_run_number(monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "42")
    monkeypatch.setenv("GITHUB_REPOSITORY", "desaivatsal/mobile-automation-framework")
    config = load_config(env="staging", platform="android", target="sauce_vdc")
    caps = build_capabilities(config)
    assert caps["sauce:options"]["build"] == "desaivatsal/mobile-automation-framework#42-staging"


def test_access_key_is_never_logged():
    config = load_config(env="qa", platform="android", target="sauce_vdc")
    caps = build_capabilities(config)
    safe = redact(caps)
    assert safe["sauce:options"]["accessKey"] == "***redacted***"
    # The original must be untouched - redact() returns a copy.
    assert caps["sauce:options"]["accessKey"] == "unit-test-key"


def test_missing_credentials_produce_a_useful_message(monkeypatch):
    monkeypatch.delenv("SAUCE_USERNAME", raising=False)
    monkeypatch.delenv("SAUCE_ACCESS_KEY", raising=False)
    config = load_config(env="qa", platform="android", target="sauce_vdc")
    with pytest.raises(ConfigError, match="user-settings"):
        build_capabilities(config)


# ---------------------------------------------------------------- endpoints
def test_hub_url_per_region():
    assert sauce_hub_url("eu-central-1").startswith("https://ondemand.eu-central-1.")
    with pytest.raises(ConfigError):
        sauce_hub_url("mars-1")


def test_local_target_uses_local_appium(monkeypatch):
    monkeypatch.setenv("APPIUM_HOST", "10.0.0.5")
    monkeypatch.setenv("APPIUM_PORT", "4725")
    config = load_config(env="qa", platform="android", target="local")
    assert remote_url(config) == "http://10.0.0.5:4725"
