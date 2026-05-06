"""Discovery routines for location-capable sources."""

from __future__ import annotations

from homeassistant.core import HomeAssistant


async def async_discover_sources(hass: HomeAssistant) -> dict[str, dict]:
    """Discover candidate location sources.

    The initial scaffold remains conservative and only returns an empty registry.
    Future implementations should inspect `person`, `device_tracker`, `zone`, and
    helper entities to build a candidate graph.
    """

    return {}

