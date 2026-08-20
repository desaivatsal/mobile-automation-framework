#!/usr/bin/env python3
"""Print every app binary in your Sauce Labs app storage.

Run this first. The output tells you exactly what to paste into
``config/apps.yaml`` - guessing a file name is the single most common cause of
"the session never starts".

    python scripts/list_sauce_apps.py
    python scripts/list_sauce_apps.py --region eu-central-1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.config_loader import ConfigError  # noqa: E402
from libs.sauce_client import SauceClient  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=None, help="Sauce data centre (default: $SAUCE_REGION)")
    args = parser.parse_args()

    try:
        client = SauceClient(args.region)
        items = client.list_apps()
    except ConfigError as exc:
        print(f"Configuration problem: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Could not reach Sauce Labs: {exc}", file=sys.stderr)
        return 1

    if not items:
        print("No apps found in Sauce app storage for this account.")
        print("Upload one with: python scripts/upload_app.py path/to/app.apk")
        return 0

    print(f"{len(items)} app(s) in {client.region}:\n")
    for item in items:
        metadata = item.get("metadata") or {}
        platform = "android" if str(item.get("name", "")).endswith((".apk", ".aab")) else "ios"
        print(f"  name        : {item.get('name')}")
        print(f"  id          : {item.get('id')}")
        print(f"  platform    : {platform}")
        print(f"  version     : {metadata.get('version')} (build {metadata.get('version_code')})")
        identifier = metadata.get("identifier")
        if identifier:
            key = "app_package" if platform == "android" else "bundle_id"
            print(f"  {key:<12}: {identifier}")
        print(f"  uploaded    : {item.get('upload_timestamp')}")
        print("  -> config/apps.yaml:")
        print(f'       storage: "storage:filename={item.get("name")}"')
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
