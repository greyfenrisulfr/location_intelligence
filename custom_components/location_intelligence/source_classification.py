"""Source classification helpers."""

from __future__ import annotations

from collections.abc import Mapping


def classify_source(entity_id: str, attributes: Mapping[str, object]) -> str:
    """Classify a Home Assistant entity into a coarse source category."""

    if entity_id.startswith("person."):
        return "person"
    if entity_id.startswith("device_tracker."):
        return "device_tracker"
    if entity_id.startswith("zone."):
        return "static_place"
    if attributes.get("source_type") == "gps":
        return "gps"
    return "unknown"

