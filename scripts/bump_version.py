#!/usr/bin/env python3
"""Update repository version references for a release."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "location_intelligence" / "manifest.json"
CHANGELOG = ROOT / "CHANGELOG.md"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/bump_version.py X.Y.Z")
        return 1

    version = sys.argv[1]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print("version must match X.Y.Z")
        return 1

    update_json_version(MANIFEST, version)
    update_changelog(version)
    print(f"updated release version to {version}")
    return 0


def update_json_version(path: Path, version: str) -> None:
    data = json.loads(path.read_text())
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_changelog(version: str) -> None:
    content = CHANGELOG.read_text()
    marker = "## [Unreleased]"
    if marker not in content:
        raise ValueError("CHANGELOG.md is missing the Unreleased section")

    release_header = f"## [{version}] - {date.today().isoformat()}"
    if release_header in content:
        return

    replacement = f"{marker}\n\n- \n\n{release_header}"
    CHANGELOG.write_text(content.replace(marker, replacement, 1))


if __name__ == "__main__":
    raise SystemExit(main())
