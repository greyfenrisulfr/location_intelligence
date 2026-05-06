#!/usr/bin/env python3
"""Validate that release versions are aligned before publishing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "location_intelligence" / "manifest.json"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/validate_release.py X.Y.Z")
        return 1

    version = sys.argv[1]
    manifest_version = load_version(MANIFEST)

    mismatches: list[str] = []
    if manifest_version != version:
        mismatches.append(f"manifest.json version is {manifest_version}, expected {version}")

    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
        return 1

    print(f"validated release version {version}")
    return 0


def load_version(path: Path) -> str:
    data = json.loads(path.read_text())
    return str(data["version"])


if __name__ == "__main__":
    raise SystemExit(main())
