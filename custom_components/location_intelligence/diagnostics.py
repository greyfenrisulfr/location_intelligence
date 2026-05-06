"""Diagnostics support for Location Intelligence."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""

    runtime = getattr(entry, "runtime_data", None)
    data = {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "domain": entry.domain,
        },
        "discovered_source_count": len(runtime.discovered_sources) if runtime else 0,
        "discovered_sources": runtime.discovered_sources if runtime else {},
        "subjects": runtime.subject_registry.subjects() if runtime else [],
        "links": runtime.subject_registry.as_dict() if runtime else {},
        "places": {
            place_id: {
                "name": place.name,
                "kind": place.kind,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "target_subject_id": place.target_subject_id,
            }
            for place_id, place in (runtime.places.items() if runtime else [])
        },
        "subject_reference_places": runtime.subject_reference_places if runtime else {},
        "recent_fix_counts": {
            subject_id: {
                source_id: len(fixes) for source_id, fixes in source_fixes.items()
            }
            for subject_id, source_fixes in (runtime.recent_fixes.items() if runtime else [])
        },
        "latest_estimates": {
            subject_id: {
                "latitude": estimate.latitude,
                "longitude": estimate.longitude,
                "confidence": estimate.confidence,
                "confidence_label": estimate.confidence_label,
                "source_count": estimate.source_count,
                "accuracy_m": estimate.accuracy_m,
                "reference_place_id": estimate.reference_place_id,
                "reference_place_name": estimate.reference_place_name,
                "reference_place_kind": estimate.reference_place_kind,
                "distance_from_reference_m": estimate.distance_from_reference_m,
                "bearing_from_reference_deg": estimate.bearing_from_reference_deg,
                "direction_from_reference": estimate.direction_from_reference,
                "distance_from_home_m": estimate.distance_from_home_m,
                "bearing_from_home_deg": estimate.bearing_from_home_deg,
                "direction_from_home": estimate.direction_from_home,
                "rationale": estimate.rationale,
            }
            for subject_id, estimate in (runtime.latest_estimates.items() if runtime else [])
        },
    }
    return async_redact_data(data, TO_REDACT)
