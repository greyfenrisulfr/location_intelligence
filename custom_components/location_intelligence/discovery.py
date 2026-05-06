"""Discovery routines for location-capable sources."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .location_helpers import extract_location_fix
from .source_classification import classify_source


async def async_discover_sources(
    hass: HomeAssistant, excluded_person_entities: set[str] | None = None
) -> dict[str, dict]:
    """Discover candidate location sources from existing HA entities."""

    entity_registry = async_get_entity_registry(hass)
    sources: dict[str, dict] = {}
    excluded_person_entities = excluded_person_entities or set()

    for domain in ("person", "device_tracker", "zone"):
        for entity_id in hass.states.async_entity_ids(domain):
            if domain == "person" and entity_id in excluded_person_entities:
                continue
            state = hass.states.get(entity_id)
            if state is None:
                continue

            classification = classify_source(entity_id, state.attributes)
            registry_entry = entity_registry.async_get(entity_id)
            device_id = registry_entry.device_id if registry_entry else None

            source = {
                "source_id": entity_id,
                "entity_id": entity_id,
                "name": state.name or entity_id,
                "classification": classification,
                "device_id": device_id,
                "state": state.state,
                "last_updated": state.last_updated.isoformat(),
            }

            fix = extract_location_fix(entity_id, state.attributes)
            if fix is not None:
                source["fix"] = {
                    "latitude": fix.latitude,
                    "longitude": fix.longitude,
                    "accuracy_m": fix.accuracy_m,
                    "confidence": fix.confidence,
                    "speed_m_s": fix.speed_m_s,
                    "observed_at": fix.observed_at.isoformat(),
                }

            linked_source = state.attributes.get("source")
            if isinstance(linked_source, str):
                source["linked_source"] = linked_source

            sources[entity_id] = source

    return sources
