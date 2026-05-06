"""Pure helpers for reference places and recent fixes."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from .models import LocationFix, ReferencePlace, ResolvedPlace, SubjectEstimate


def serialize_fix(fix: LocationFix) -> dict[str, float | str | None]:
    """Serialize a fix for storage."""

    return {
        "latitude": fix.latitude,
        "longitude": fix.longitude,
        "accuracy_m": fix.accuracy_m,
        "confidence": fix.confidence,
        "speed_m_s": fix.speed_m_s,
        "observed_at": fix.observed_at.isoformat(),
    }


def deserialize_fix(data: Mapping[str, object]) -> LocationFix:
    """Deserialize a fix from storage."""

    observed_at = data.get("observed_at")
    if isinstance(observed_at, str):
        parsed = datetime.fromisoformat(observed_at)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        else:
            parsed = parsed.astimezone(UTC)
    else:
        parsed = datetime.now(UTC)

    return LocationFix(
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        accuracy_m=_optional_float(data.get("accuracy_m")),
        confidence=_optional_float(data.get("confidence")),
        speed_m_s=_optional_float(data.get("speed_m_s")),
        observed_at=parsed,
    )


def serialize_place(place: ReferencePlace) -> dict[str, object]:
    """Serialize a reference place for storage."""

    return {
        "place_id": place.place_id,
        "name": place.name,
        "kind": place.kind,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "target_subject_id": place.target_subject_id,
    }


def deserialize_place(data: Mapping[str, object]) -> ReferencePlace:
    """Deserialize a reference place from storage."""

    return ReferencePlace(
        place_id=str(data["place_id"]),
        name=str(data.get("name", data["place_id"])),
        kind=str(data.get("kind", "coordinates")),
        latitude=_optional_float(data.get("latitude")),
        longitude=_optional_float(data.get("longitude")),
        target_subject_id=_optional_str(data.get("target_subject_id")),
    )


def remember_recent_fix(
    recent_fixes: dict[str, dict[str, list[LocationFix]]],
    subject_id: str,
    source_id: str,
    fix: LocationFix,
    limit: int,
) -> None:
    """Append a fix to persisted recent history with a bounded size."""

    source_history = recent_fixes.setdefault(subject_id, {}).setdefault(source_id, [])
    source_history.append(fix)
    source_history.sort(key=lambda item: item.observed_at)
    if len(source_history) > limit:
        del source_history[:-limit]


def latest_recent_fix(
    recent_fixes: Mapping[str, Mapping[str, list[LocationFix]]],
    subject_id: str,
    source_id: str | None = None,
) -> LocationFix | None:
    """Return the latest known fix for one subject."""

    subject_history = recent_fixes.get(subject_id, {})
    candidates: list[LocationFix] = []
    if source_id is not None:
        candidates.extend(subject_history.get(source_id, []))
    else:
        for fixes in subject_history.values():
            candidates.extend(fixes)
    if not candidates:
        return None
    return max(candidates, key=lambda fix: fix.observed_at)


def serialize_recent_fixes(
    recent_fixes: Mapping[str, Mapping[str, list[LocationFix]]],
) -> dict[str, dict[str, list[dict[str, object]]]]:
    """Serialize recent fixes for storage."""

    return {
        subject_id: {
            source_id: [serialize_fix(fix) for fix in fixes]
            for source_id, fixes in source_fixes.items()
        }
        for subject_id, source_fixes in recent_fixes.items()
    }


def deserialize_recent_fixes(
    data: Mapping[str, Mapping[str, list[Mapping[str, object]]]] | None,
) -> dict[str, dict[str, list[LocationFix]]]:
    """Deserialize recent fixes from storage."""

    recent_fixes: dict[str, dict[str, list[LocationFix]]] = {}
    if not data:
        return recent_fixes

    for subject_id, source_fixes in data.items():
        recent_fixes[subject_id] = {
            source_id: [deserialize_fix(fix) for fix in fixes]
            for source_id, fixes in source_fixes.items()
        }
    return recent_fixes


def resolve_reference_place(
    subject_id: str,
    subject_reference_places: Mapping[str, str],
    places: Mapping[str, ReferencePlace],
    latest_estimates: Mapping[str, SubjectEstimate],
    recent_fixes: Mapping[str, Mapping[str, list[LocationFix]]],
    home_coordinates: tuple[float, float] | None,
) -> ResolvedPlace | None:
    """Resolve the active reference place for a subject."""

    place_id = subject_reference_places.get(subject_id)
    if place_id:
        place = places.get(place_id)
        resolved = resolve_place(place, latest_estimates, recent_fixes) if place else None
        if resolved is not None:
            return resolved

    if home_coordinates is None:
        return None
    return ResolvedPlace(
        place_id="home",
        name="Home",
        kind="home",
        latitude=home_coordinates[0],
        longitude=home_coordinates[1],
    )


def resolve_place(
    place: ReferencePlace | None,
    latest_estimates: Mapping[str, SubjectEstimate],
    recent_fixes: Mapping[str, Mapping[str, list[LocationFix]]],
) -> ResolvedPlace | None:
    """Resolve a place definition into concrete coordinates."""

    if place is None:
        return None

    if place.kind == "coordinates":
        if place.latitude is None or place.longitude is None:
            return None
        return ResolvedPlace(
            place_id=place.place_id,
            name=place.name,
            kind=place.kind,
            latitude=place.latitude,
            longitude=place.longitude,
        )

    if place.kind == "subject":
        if place.target_subject_id is None:
            return None
        estimate = latest_estimates.get(place.target_subject_id)
        if estimate is None:
            return None
        return ResolvedPlace(
            place_id=place.place_id,
            name=place.name,
            kind=place.kind,
            latitude=estimate.latitude,
            longitude=estimate.longitude,
        )

    if place.kind == "last_known":
        if place.target_subject_id is None:
            return None
        fix = latest_recent_fix(recent_fixes, place.target_subject_id)
        if fix is None:
            return None
        return ResolvedPlace(
            place_id=place.place_id,
            name=place.name,
            kind=place.kind,
            latitude=fix.latitude,
            longitude=fix.longitude,
        )

    return None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
