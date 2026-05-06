"""Sensor platform for Location Intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LocationIntelligenceRuntime
from .entity import LocationIntelligenceEntity


@dataclass(frozen=True, kw_only=True)
class LocationIntelligenceSensorDescription(SensorEntityDescription):
    """Describe a static scaffold sensor."""

    value_key: str


DESCRIPTIONS: tuple[LocationIntelligenceSensorDescription, ...] = (
    LocationIntelligenceSensorDescription(
        key="discovered_sources",
        name="Discovered Sources",
        icon="mdi:crosshairs-gps",
        value_key="discovered_sources",
    ),
    LocationIntelligenceSensorDescription(
        key="tracked_subjects",
        name="Tracked Subjects",
        icon="mdi:map-marker-account",
        value_key="tracked_subjects",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[LocationIntelligenceRuntime],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for the config entry."""

    async_add_entities(
        LocationIntelligenceSensor(runtime=entry.runtime_data, description=description)
        for description in DESCRIPTIONS
    )


class LocationIntelligenceSensor(LocationIntelligenceEntity, SensorEntity):
    """Expose high-level backend state."""

    entity_description: LocationIntelligenceSensorDescription

    def __init__(
        self,
        runtime: LocationIntelligenceRuntime,
        description: LocationIntelligenceSensorDescription,
    ) -> None:
        self._runtime = runtime
        self.entity_description = description
        self._attr_unique_id = f"location_intelligence_{description.key}"

    @property
    def native_value(self) -> int:
        """Return the current value."""

        if self.entity_description.value_key == "discovered_sources":
            return len(self._runtime.discovered_sources)
        if self.entity_description.value_key == "tracked_subjects":
            return len(self._runtime.subject_registry.subjects())
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return explainable state attributes."""

        if self.entity_description.value_key == "tracked_subjects":
            return {"subjects": self._runtime.subject_registry.subjects()}
        return {}

