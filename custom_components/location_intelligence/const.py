"""Constants for Location Intelligence."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.const import Platform
else:
    Platform = str

DOMAIN = "location_intelligence"
NAME = "Location Intelligence"
STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN

PLATFORMS: list[Platform] = ["sensor"]

DEFAULT_ENTRY_NAME = "Location Intelligence"


def update_signal(entry_id: str) -> str:
    """Return the dispatcher signal for runtime updates."""

    return f"{DOMAIN}_updated_{entry_id}"


def subjects_signal(entry_id: str) -> str:
    """Return the dispatcher signal for subject lifecycle updates."""

    return f"{DOMAIN}_subjects_{entry_id}"
