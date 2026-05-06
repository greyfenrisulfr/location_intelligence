"""Pure helpers for extracting and enriching location data."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from math import isfinite

from .models import LocationFix


def extract_location_fix(
    entity_id: str, attributes: Mapping[str, object]
) -> LocationFix | None:
    """Extract a conservative fix from Home Assistant-like state attributes."""

    latitude = _coerce_float(attributes.get("latitude"))
    longitude = _coerce_float(attributes.get("longitude"))
    if latitude is None or longitude is None:
        return None

    observed_at = _coerce_datetime(attributes.get("last_seen")) or datetime.now(UTC)
    return LocationFix(
        latitude=latitude,
        longitude=longitude,
        accuracy_m=_coerce_float(attributes.get("gps_accuracy")),
        confidence=_default_confidence(entity_id, attributes),
        speed_m_s=_coerce_float(attributes.get("speed")),
        observed_at=observed_at,
    )


def _default_confidence(entity_id: str, attributes: Mapping[str, object]) -> float:
    if entity_id.startswith("person."):
        return 0.75
    source_type = attributes.get("source_type")
    if source_type == "gps":
        return 0.85
    if source_type == "router":
        return 0.5
    return 0.6


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result):
        return None
    return result


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None
