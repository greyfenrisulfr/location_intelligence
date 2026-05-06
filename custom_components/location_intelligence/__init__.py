"""Location Intelligence integration."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform

from .const import DOMAIN
from .discovery import async_discover_sources
from .models import LocationFix, SubjectEstimate
from .subject_mapping import SubjectRegistry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class LocationIntelligenceRuntime:
    """Runtime state for the integration."""

    discovered_sources: dict[str, dict] = field(default_factory=dict)
    subject_registry: SubjectRegistry = field(default_factory=SubjectRegistry)
    latest_estimates: dict[str, SubjectEstimate] = field(default_factory=dict)


type LocationIntelligenceConfigEntry = ConfigEntry[LocationIntelligenceRuntime]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration from YAML."""

    async def handle_refresh(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Refresh requested without an active config entry")
            return

        runtime.discovered_sources = await async_discover_sources(hass)

    async def handle_ingest_fix(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Fix ingestion requested without an active config entry")
            return

        subject_id = call.data["subject_id"]
        source_id = call.data["source_id"]
        source_name = call.data.get("source_name", source_id)
        fix = LocationFix(
            latitude=call.data["latitude"],
            longitude=call.data["longitude"],
            accuracy_m=call.data.get("accuracy_m"),
            confidence=call.data.get("confidence"),
            speed_m_s=call.data.get("speed_m_s"),
        )
        runtime.subject_registry.link_source(subject_id, source_id, source_name)
        runtime.latest_estimates[subject_id] = runtime.subject_registry.ingest_fix(
            subject_id=subject_id,
            source_id=source_id,
            fix=fix,
        )

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    hass.services.async_register(DOMAIN, "ingest_fix", handle_ingest_fix)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: LocationIntelligenceConfigEntry
) -> bool:
    """Set up Location Intelligence from a config entry."""

    runtime = LocationIntelligenceRuntime()
    runtime.discovered_sources = await async_discover_sources(hass)
    entry.runtime_data = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LocationIntelligenceConfigEntry
) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _first_runtime(hass: HomeAssistant) -> LocationIntelligenceRuntime | None:
    """Return the first loaded runtime state."""

    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime
    return None

