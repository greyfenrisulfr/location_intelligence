"""Sensor platform for Location Intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import subjects_signal, update_signal
from .entity import LocationIntelligenceEntity
from .runtime import LocationIntelligenceRuntime


@dataclass(frozen=True, kw_only=True)
class LocationIntelligenceSensorDescription(SensorEntityDescription):
    """Describe an aggregate sensor."""

    value_key: str


@dataclass(frozen=True, kw_only=True)
class SubjectSensorDescription(SensorEntityDescription):
    """Describe one subject-centric sensor."""

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

SUBJECT_DESCRIPTIONS: tuple[SubjectSensorDescription, ...] = (
    SubjectSensorDescription(
        key="status",
        name="Status",
        icon="mdi:map-marker-radius",
        value_key="status",
    ),
    SubjectSensorDescription(
        key="distance_from_home",
        name="Distance From Home",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement="m",
        value_key="distance_from_home",
    ),
    SubjectSensorDescription(
        key="direction_from_home",
        name="Direction From Home",
        icon="mdi:compass-outline",
        value_key="direction_from_home",
    ),
    SubjectSensorDescription(
        key="reference_place",
        name="Reference Place",
        icon="mdi:map-marker-check-outline",
        value_key="reference_place",
    ),
    SubjectSensorDescription(
        key="distance_from_reference",
        name="Distance From Reference",
        icon="mdi:map-marker-path",
        native_unit_of_measurement="m",
        value_key="distance_from_reference",
    ),
    SubjectSensorDescription(
        key="direction_from_reference",
        name="Direction From Reference",
        icon="mdi:compass-rose",
        value_key="direction_from_reference",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[LocationIntelligenceRuntime],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for the config entry."""

    runtime = entry.runtime_data
    known_subjects: set[str] = set()

    async_add_entities(
        [LocationIntelligenceSensor(runtime=runtime, description=description) for description in DESCRIPTIONS]
    )

    def build_subject_entities() -> list[SubjectEstimateSensor]:
        entities: list[SubjectEstimateSensor] = []
        for subject_id in runtime.subject_registry.subjects():
            if subject_id in known_subjects:
                continue
            known_subjects.add(subject_id)
            for description in SUBJECT_DESCRIPTIONS:
                entities.append(
                    SubjectEstimateSensor(
                        runtime=runtime,
                        subject_id=subject_id,
                        description=description,
                    )
                )
        return entities

    initial_entities = build_subject_entities()
    if initial_entities:
        async_add_entities(initial_entities)

    async def async_add_new_subject_entities() -> None:
        """Add newly discovered subject sensors in a task context."""

        entities = build_subject_entities()
        if entities:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            subjects_signal(entry.entry_id),
            lambda: hass.add_job(async_add_new_subject_entities),
        )
    )


class RuntimeBackedSensor(LocationIntelligenceEntity, SensorEntity):
    """Base sensor that listens for runtime updates."""

    _attr_should_poll = False

    def __init__(self, runtime: LocationIntelligenceRuntime) -> None:
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime updates."""

        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                update_signal(self._runtime.entry_id),
                self._handle_runtime_update,
            )
        )

    @callback
    def _handle_runtime_update(self) -> None:
        self.async_write_ha_state()


class LocationIntelligenceSensor(RuntimeBackedSensor):
    """Expose high-level backend state."""

    entity_description: LocationIntelligenceSensorDescription

    def __init__(
        self,
        runtime: LocationIntelligenceRuntime,
        description: LocationIntelligenceSensorDescription,
    ) -> None:
        super().__init__(runtime)
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

        if self.entity_description.value_key == "discovered_sources":
            return {"sources": sorted(self._runtime.discovered_sources)}
        if self.entity_description.value_key == "tracked_subjects":
            return {"subjects": self._runtime.subject_registry.subjects()}
        return {}


class SubjectEstimateSensor(RuntimeBackedSensor):
    """Expose per-subject derived state."""

    entity_description: SubjectSensorDescription

    def __init__(
        self,
        runtime: LocationIntelligenceRuntime,
        subject_id: str,
        description: SubjectSensorDescription,
    ) -> None:
        super().__init__(runtime)
        self.entity_description = description
        self._subject_id = subject_id
        self._attr_unique_id = f"location_intelligence_{subject_id}_{description.key}"
        self._attr_has_entity_name = False
        self._attr_name = f"{subject_id} {description.name}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return whether a subject estimate exists."""

        return self._subject_id in self._runtime.latest_estimates

    @property
    def native_value(self) -> str | float | None:
        """Return the current derived value."""

        estimate = self._runtime.latest_estimates.get(self._subject_id)
        if estimate is None:
            return None
        if self.entity_description.value_key == "status":
            return estimate.confidence_label
        if self.entity_description.value_key == "distance_from_home":
            return estimate.distance_from_home_m
        if self.entity_description.value_key == "direction_from_home":
            return estimate.direction_from_home
        if self.entity_description.value_key == "reference_place":
            return estimate.reference_place_name
        if self.entity_description.value_key == "distance_from_reference":
            return estimate.distance_from_reference_m
        if self.entity_description.value_key == "direction_from_reference":
            return estimate.direction_from_reference
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose explainable estimate details."""

        estimate = self._runtime.latest_estimates.get(self._subject_id)
        if estimate is None:
            return {}
        attributes: dict[str, object] = {
            "subject_id": self._subject_id,
            "latitude": estimate.latitude,
            "longitude": estimate.longitude,
            "confidence": estimate.confidence,
            "confidence_label": estimate.confidence_label,
            "source_count": estimate.source_count,
            "accuracy_m": estimate.accuracy_m,
            "observed_at": estimate.observed_at.isoformat(),
            "rationale": estimate.rationale,
        }
        if estimate.reference_place_id is not None:
            attributes["reference_place_id"] = estimate.reference_place_id
        if estimate.reference_place_name is not None:
            attributes["reference_place_name"] = estimate.reference_place_name
        if estimate.reference_place_kind is not None:
            attributes["reference_place_kind"] = estimate.reference_place_kind
        if estimate.distance_from_reference_m is not None:
            attributes["distance_from_reference_m"] = estimate.distance_from_reference_m
        if estimate.bearing_from_reference_deg is not None:
            attributes["bearing_from_reference_deg"] = estimate.bearing_from_reference_deg
        if estimate.direction_from_reference is not None:
            attributes["direction_from_reference"] = estimate.direction_from_reference
        if estimate.distance_from_home_m is not None:
            attributes["distance_from_home_m"] = estimate.distance_from_home_m
        if estimate.bearing_from_home_deg is not None:
            attributes["bearing_from_home_deg"] = estimate.bearing_from_home_deg
        if estimate.direction_from_home is not None:
            attributes["direction_from_home"] = estimate.direction_from_home
        return attributes
