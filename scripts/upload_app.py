#!/usr/bin/env python3
"""Upload an app binary to Sauce Labs app storage.

App binaries must never be committed to this repository - they bloat clones and
go stale immediately. Build them in your app pipeline, upload here, and
reference the file name from ``config/apps.yaml``.

    python scripts/upload_app.py build/app-qa.apk
    python scripts/upload_app.py build/app-qa.apk --description "QA build 1.4.2"
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
    parser.add_argument("path", help="Path to the .apk / .ipa / .zip")
    parser.add_argument("--description", default="", help="Free-text description")
    parser.add_argument("--region", default=None, help="Sauce data centre (default: $SAUCE_REGION)")
    args = parser.parse_args()

    try:
        item = SauceClient(args.region).upload_app(args.path, args.description)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"{exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1

    print("Uploaded.")
    print(f"  name : {item.get('name')}")
    print(f"  id   : {item.get('id')}")
    print("\nReference it in config/apps.yaml as:")
    print(f'  storage: "storage:filename={item.get("name")}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
