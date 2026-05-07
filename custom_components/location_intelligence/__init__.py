"""Location Intelligence integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import logging

from .const import DOMAIN
from .models import LocationFix

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.helpers.typing import ConfigType

    from .runtime import LocationIntelligenceRuntime

    type LocationIntelligenceConfigEntry = ConfigEntry[LocationIntelligenceRuntime]
else:
    HomeAssistant = Any
    ServiceCall = Any
    ConfigType = dict[str, Any]
    LocationIntelligenceConfigEntry = Any

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration from YAML."""

    import voluptuous as vol

    SERVICE_INGEST_FIX_SCHEMA = vol.Schema(
        {
            vol.Required("subject_id"): str,
            vol.Required("source_id"): str,
            vol.Required("latitude"): vol.Coerce(float),
            vol.Required("longitude"): vol.Coerce(float),
            vol.Optional("source_name"): str,
            vol.Optional("source_type", default="manual"): str,
            vol.Optional("accuracy_m"): vol.Coerce(float),
            vol.Optional("confidence"): vol.Coerce(float),
            vol.Optional("speed_m_s"): vol.Coerce(float),
        }
    )
    SERVICE_LINK_SOURCE_SCHEMA = vol.Schema(
        {
            vol.Required("subject_id"): str,
            vol.Required("source_id"): str,
            vol.Optional("source_name"): str,
            vol.Optional("source_type", default="manual"): str,
        }
    )
    SERVICE_UPSERT_PLACE_SCHEMA = vol.Schema(
        {
            vol.Required("place_id"): str,
            vol.Optional("place_name"): str,
            vol.Optional("kind", default="coordinates"): str,
            vol.Optional("latitude"): vol.Coerce(float),
            vol.Optional("longitude"): vol.Coerce(float),
            vol.Optional("target_subject_id"): str,
        }
    )
    SERVICE_ASSIGN_REFERENCE_PLACE_SCHEMA = vol.Schema(
        {
            vol.Required("subject_id"): str,
            vol.Required("place_id"): str,
        }
    )
    SERVICE_REMOVE_PLACE_SCHEMA = vol.Schema({vol.Required("place_id"): str})
    SERVICE_CLEAR_REFERENCE_PLACE_SCHEMA = vol.Schema({vol.Required("subject_id"): str})
    SERVICE_PERSON_ENTITY_SCHEMA = vol.Schema({vol.Required("entity_id"): str})
    SERVICE_CLEAR_SUBJECT_SCHEMA = vol.Schema({vol.Required("subject_id"): str})

    async def handle_refresh(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Refresh requested without an active config entry")
            return
        await runtime.async_refresh()

    async def handle_ingest_fix(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Fix ingestion requested without an active config entry")
            return

        source_id = call.data["source_id"]
        await runtime.async_ingest_fix(
            subject_id=call.data["subject_id"],
            source_id=source_id,
            source_name=call.data.get("source_name", source_id),
            source_type=call.data.get("source_type", "manual"),
            fix=LocationFix(
                latitude=call.data["latitude"],
                longitude=call.data["longitude"],
                accuracy_m=call.data.get("accuracy_m"),
                confidence=call.data.get("confidence"),
                speed_m_s=call.data.get("speed_m_s"),
            ),
        )

    async def handle_link_source(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Link requested without an active config entry")
            return

        source_id = call.data["source_id"]
        await runtime.async_link_source(
            subject_id=call.data["subject_id"],
            source_id=source_id,
            source_name=call.data.get("source_name", source_id),
            source_type=call.data.get("source_type", "manual"),
        )

    async def handle_clear_subject(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Clear subject requested without an active config entry")
            return
        await runtime.async_clear_subject(call.data["subject_id"])

    async def handle_upsert_place(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Upsert place requested without an active config entry")
            return

        place_id = call.data["place_id"]
        await runtime.async_upsert_place(
            place_id=place_id,
            place_name=call.data.get("place_name", place_id),
            kind=call.data.get("kind", "coordinates"),
            latitude=call.data.get("latitude"),
            longitude=call.data.get("longitude"),
            target_subject_id=call.data.get("target_subject_id"),
        )

    async def handle_assign_reference_place(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Assign reference place requested without an active config entry")
            return
        await runtime.async_assign_reference_place(
            call.data["subject_id"], call.data["place_id"]
        )

    async def handle_remove_place(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Remove place requested without an active config entry")
            return
        await runtime.async_remove_place(call.data["place_id"])

    async def handle_clear_reference_place(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Clear reference place requested without an active config entry")
            return
        await runtime.async_clear_reference_place(call.data["subject_id"])

    async def handle_exclude_person_entity(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Exclude person requested without an active config entry")
            return
        await runtime.async_exclude_person_entity(call.data["entity_id"])

    async def handle_include_person_entity(call: ServiceCall) -> None:
        runtime = _first_runtime(hass)
        if runtime is None:
            _LOGGER.debug("Include person requested without an active config entry")
            return
        await runtime.async_include_person_entity(call.data["entity_id"])

    if not hass.services.has_service(DOMAIN, "refresh"):
        hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    if not hass.services.has_service(DOMAIN, "ingest_fix"):
        hass.services.async_register(
            DOMAIN, "ingest_fix", handle_ingest_fix, schema=SERVICE_INGEST_FIX_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, "link_source"):
        hass.services.async_register(
            DOMAIN, "link_source", handle_link_source, schema=SERVICE_LINK_SOURCE_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, "upsert_place"):
        hass.services.async_register(
            DOMAIN, "upsert_place", handle_upsert_place, schema=SERVICE_UPSERT_PLACE_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, "assign_reference_place"):
        hass.services.async_register(
            DOMAIN,
            "assign_reference_place",
            handle_assign_reference_place,
            schema=SERVICE_ASSIGN_REFERENCE_PLACE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "remove_place"):
        hass.services.async_register(
            DOMAIN, "remove_place", handle_remove_place, schema=SERVICE_REMOVE_PLACE_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, "clear_reference_place"):
        hass.services.async_register(
            DOMAIN,
            "clear_reference_place",
            handle_clear_reference_place,
            schema=SERVICE_CLEAR_REFERENCE_PLACE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "exclude_person_entity"):
        hass.services.async_register(
            DOMAIN,
            "exclude_person_entity",
            handle_exclude_person_entity,
            schema=SERVICE_PERSON_ENTITY_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "include_person_entity"):
        hass.services.async_register(
            DOMAIN,
            "include_person_entity",
            handle_include_person_entity,
            schema=SERVICE_PERSON_ENTITY_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "clear_subject"):
        hass.services.async_register(
            DOMAIN, "clear_subject", handle_clear_subject, schema=SERVICE_CLEAR_SUBJECT_SCHEMA
        )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: LocationIntelligenceConfigEntry
) -> bool:
    """Set up Location Intelligence from a config entry."""

    from .runtime import LocationIntelligenceRuntime

    runtime = LocationIntelligenceRuntime(hass=hass, entry_id=entry.entry_id)
    await runtime.async_initialize()
    entry.runtime_data = runtime
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LocationIntelligenceConfigEntry
) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _first_runtime(hass: HomeAssistant) -> Any | None:
    """Return the first loaded runtime state."""

    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime
    return None


async def _async_options_updated(
    hass: HomeAssistant, entry: LocationIntelligenceConfigEntry
) -> None:
    """Reload the config entry after options change."""

    await hass.config_entries.async_reload(entry.entry_id)
