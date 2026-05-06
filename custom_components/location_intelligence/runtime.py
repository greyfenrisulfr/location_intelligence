"""Runtime manager for Location Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .calculations import bearing_deg, cardinal_direction, distance_m
from .const import (
    MAX_RECENT_FIXES,
    STORAGE_KEY,
    STORAGE_VERSION,
    subjects_signal,
    update_signal,
)
from .discovery import async_discover_sources
from .location_helpers import extract_location_fix
from .models import LocationFix, ReferencePlace, SubjectEstimate
from .place_helpers import (
    deserialize_place,
    deserialize_recent_fixes,
    latest_recent_fix,
    remember_recent_fix,
    resolve_reference_place,
    serialize_place,
    serialize_recent_fixes,
)
from .subject_mapping import SubjectRegistry


@dataclass
class LocationIntelligenceRuntime:
    """Manage runtime state, storage, and derived estimates."""

    hass: HomeAssistant
    entry_id: str
    discovered_sources: dict[str, dict] = field(default_factory=dict)
    subject_registry: SubjectRegistry = field(default_factory=SubjectRegistry)
    latest_estimates: dict[str, SubjectEstimate] = field(default_factory=dict)
    places: dict[str, ReferencePlace] = field(default_factory=dict)
    subject_reference_places: dict[str, str] = field(default_factory=dict)
    recent_fixes: dict[str, dict[str, list[LocationFix]]] = field(default_factory=dict)
    excluded_person_entities: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self._store = Store[dict](self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry_id}")

    async def async_initialize(self) -> None:
        """Load stored mappings and populate runtime state."""

        stored = await self._store.async_load()
        self.subject_registry = SubjectRegistry.from_dict(stored.get("links") if stored else None)
        self.subject_reference_places = {
            str(subject_id): str(place_id)
            for subject_id, place_id in (stored.get("subject_reference_places", {}) if stored else {}).items()
        }
        self.excluded_person_entities = {
            str(entity_id) for entity_id in (stored.get("excluded_person_entities", []) if stored else [])
        }
        self.places = {
            place_id: deserialize_place(place)
            for place_id, place in (stored.get("places", {}) if stored else {}).items()
        }
        self.recent_fixes = deserialize_recent_fixes(stored.get("recent_fixes") if stored else None)
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Refresh discovery, hydrate mappings, and rebuild estimates."""

        previous_subjects = set(self.subject_registry.subjects())
        self.discovered_sources = await async_discover_sources(
            self.hass, excluded_person_entities=self.excluded_person_entities
        )
        self._drop_excluded_person_subjects()
        self._sync_mappings_from_discovery()
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_ingest_fix(
        self,
        subject_id: str,
        source_id: str,
        source_name: str,
        fix: LocationFix,
        source_type: str = "manual",
    ) -> SubjectEstimate:
        """Store a manual fix and emit updated estimates."""

        previous_subjects = set(self.subject_registry.subjects())
        self.subject_registry.link_source(subject_id, source_id, source_name, source_type)
        estimate = self.subject_registry.ingest_fix(subject_id, source_id, fix)
        self.latest_estimates[subject_id] = self._enrich_estimate(estimate)
        remember_recent_fix(
            self.recent_fixes, subject_id, source_id, fix, limit=MAX_RECENT_FIXES
        )
        await self._async_save()
        self._async_dispatch(previous_subjects)
        return self.latest_estimates[subject_id]

    async def async_link_source(
        self,
        subject_id: str,
        source_id: str,
        source_name: str,
        source_type: str,
    ) -> None:
        """Persist a manual subject/source link."""

        previous_subjects = set(self.subject_registry.subjects())
        self.subject_registry.link_source(subject_id, source_id, source_name, source_type)
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_upsert_place(
        self,
        place_id: str,
        place_name: str,
        kind: str,
        latitude: float | None = None,
        longitude: float | None = None,
        target_subject_id: str | None = None,
    ) -> None:
        """Create or update a reference place."""

        if kind not in {"coordinates", "subject", "last_known"}:
            raise ValueError(f"Unsupported place kind: {kind}")
        if kind == "coordinates" and (latitude is None or longitude is None):
            raise ValueError("Coordinate places require latitude and longitude")
        if kind in {"subject", "last_known"} and not target_subject_id:
            raise ValueError(f"{kind} places require target_subject_id")

        previous_subjects = set(self.subject_registry.subjects())
        self.places[place_id] = ReferencePlace(
            place_id=place_id,
            name=place_name,
            kind=kind,
            latitude=latitude,
            longitude=longitude,
            target_subject_id=target_subject_id,
        )
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_remove_place(self, place_id: str) -> None:
        """Delete a reference place and any assignments to it."""

        previous_subjects = set(self.subject_registry.subjects())
        self.places.pop(place_id, None)
        self.subject_reference_places = {
            subject_id: assigned_place_id
            for subject_id, assigned_place_id in self.subject_reference_places.items()
            if assigned_place_id != place_id
        }
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_assign_reference_place(self, subject_id: str, place_id: str) -> None:
        """Assign a place as the subject-specific reference."""

        if place_id not in self.places:
            raise ValueError(f"Unknown place_id: {place_id}")
        previous_subjects = set(self.subject_registry.subjects())
        self.subject_reference_places[subject_id] = place_id
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_clear_reference_place(self, subject_id: str) -> None:
        """Return a subject to the default home reference place."""

        previous_subjects = set(self.subject_registry.subjects())
        self.subject_reference_places.pop(subject_id, None)
        self._rebuild_estimates_from_discovery()
        await self._async_save()
        self._async_dispatch(previous_subjects)

    async def async_exclude_person_entity(self, entity_id: str) -> None:
        """Exclude a person entity from discovery and derived subjects."""

        self.excluded_person_entities.add(entity_id)
        await self.async_refresh()

    async def async_include_person_entity(self, entity_id: str) -> None:
        """Remove a person entity from the exclusion list."""

        self.excluded_person_entities.discard(entity_id)
        await self.async_refresh()

    async def async_clear_subject(self, subject_id: str) -> None:
        """Remove all data for one subject."""

        previous_subjects = set(self.subject_registry.subjects())
        self.subject_registry.clear_subject(subject_id)
        self.latest_estimates.pop(subject_id, None)
        self.subject_reference_places.pop(subject_id, None)
        self.recent_fixes.pop(subject_id, None)
        await self._async_save()
        self._async_dispatch(previous_subjects)

    def _sync_mappings_from_discovery(self) -> None:
        claimed_sources = {
            source["linked_source"]
            for source in self.discovered_sources.values()
            if source["source_id"].startswith("person.")
            and isinstance(source.get("linked_source"), str)
            and source["linked_source"] in self.discovered_sources
        }

        for source_id, source in self.discovered_sources.items():
            source_name = source["name"]
            source_type = source["classification"]

            if source_id.startswith("person."):
                self.subject_registry.link_source(source_id, source_id, source_name, source_type)
                linked_source = source.get("linked_source")
                if isinstance(linked_source, str) and linked_source in self.discovered_sources:
                    linked = self.discovered_sources[linked_source]
                    self.subject_registry.link_source(
                        source_id,
                        linked_source,
                        linked["name"],
                        linked["classification"],
                    )
                continue

            if source_id.startswith("device_tracker."):
                if source_id in claimed_sources:
                    continue
                if not any(
                    link.source_id == source_id for link in self.subject_registry.iter_links()
                ):
                    self.subject_registry.link_source(
                        source_id, source_id, source_name, source_type
                    )

    def _drop_excluded_person_subjects(self) -> None:
        """Remove excluded person subjects and their transient state."""

        for entity_id in self.excluded_person_entities:
            self.subject_registry.clear_subject(entity_id)
            self.latest_estimates.pop(entity_id, None)
            self.subject_reference_places.pop(entity_id, None)
            self.recent_fixes.pop(entity_id, None)

    def _rebuild_estimates_from_discovery(self) -> None:
        self.subject_registry.clear_fixes()
        latest_estimates: dict[str, SubjectEstimate] = {}

        for subject_id in self.subject_registry.subjects():
            for link in self.subject_registry.links_for_subject(subject_id):
                state = self.hass.states.get(link.source_id)
                attributes = state.attributes if state is not None else {}
                fix = extract_location_fix(link.source_id, attributes)
                if fix is None:
                    fix = latest_recent_fix(self.recent_fixes, subject_id, link.source_id)
                    if fix is None:
                        continue
                else:
                    remember_recent_fix(
                        self.recent_fixes,
                        subject_id,
                        link.source_id,
                        fix,
                        limit=MAX_RECENT_FIXES,
                    )
                latest_estimates[subject_id] = self.subject_registry.ingest_fix(
                    subject_id, link.source_id, fix
                )

        self.latest_estimates = latest_estimates
        self.latest_estimates = {
            subject_id: self._enrich_estimate(estimate, self.latest_estimates)
            for subject_id, estimate in self.latest_estimates.items()
        }

    def _enrich_estimate(
        self,
        estimate: SubjectEstimate,
        estimates: dict[str, SubjectEstimate] | None = None,
    ) -> SubjectEstimate:
        home_latitude = getattr(self.hass.config, ATTR_LATITUDE, None)
        home_longitude = getattr(self.hass.config, ATTR_LONGITUDE, None)
        if home_latitude is not None and home_longitude is not None:
            estimate.distance_from_home_m = round(
                distance_m(home_latitude, home_longitude, estimate.latitude, estimate.longitude), 1
            )
            estimate.bearing_from_home_deg = round(
                bearing_deg(home_latitude, home_longitude, estimate.latitude, estimate.longitude), 1
            )
            estimate.direction_from_home = cardinal_direction(estimate.bearing_from_home_deg)

        home_coordinates = None
        if home_latitude is not None and home_longitude is not None:
            home_coordinates = (float(home_latitude), float(home_longitude))

        reference_place = resolve_reference_place(
            subject_id=estimate.subject_id,
            subject_reference_places=self.subject_reference_places,
            places=self.places,
            latest_estimates=estimates or (self.latest_estimates | {estimate.subject_id: estimate}),
            recent_fixes=self.recent_fixes,
            home_coordinates=home_coordinates,
        )
        if reference_place is not None:
            estimate.reference_place_id = reference_place.place_id
            estimate.reference_place_name = reference_place.name
            estimate.reference_place_kind = reference_place.kind
            estimate.distance_from_reference_m = round(
                distance_m(
                    reference_place.latitude,
                    reference_place.longitude,
                    estimate.latitude,
                    estimate.longitude,
                ),
                1,
            )
            estimate.bearing_from_reference_deg = round(
                bearing_deg(
                    reference_place.latitude,
                    reference_place.longitude,
                    estimate.latitude,
                    estimate.longitude,
                ),
                1,
            )
            estimate.direction_from_reference = cardinal_direction(
                estimate.bearing_from_reference_deg
            )
            estimate.rationale = [
                *estimate.rationale,
                f"reference place {reference_place.name} ({reference_place.kind})",
            ]
        return estimate

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "links": self.subject_registry.as_dict(),
                "places": {
                    place_id: serialize_place(place) for place_id, place in self.places.items()
                },
                "subject_reference_places": self.subject_reference_places,
                "recent_fixes": serialize_recent_fixes(self.recent_fixes),
                "excluded_person_entities": sorted(self.excluded_person_entities),
            }
        )

    def _async_dispatch(self, previous_subjects: set[str]) -> None:
        async_dispatcher_send(self.hass, update_signal(self.entry_id))
        current_subjects = set(self.subject_registry.subjects())
        if current_subjects != previous_subjects:
            async_dispatcher_send(self.hass, subjects_signal(self.entry_id))
