"""Runtime manager for Location Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .calculations import bearing_deg, cardinal_direction, distance_m
from .const import STORAGE_KEY, STORAGE_VERSION, subjects_signal, update_signal
from .discovery import async_discover_sources
from .location_helpers import extract_location_fix
from .models import LocationFix, SubjectEstimate
from .subject_mapping import SubjectRegistry


@dataclass
class LocationIntelligenceRuntime:
    """Manage runtime state, storage, and derived estimates."""

    hass: HomeAssistant
    entry_id: str
    discovered_sources: dict[str, dict] = field(default_factory=dict)
    subject_registry: SubjectRegistry = field(default_factory=SubjectRegistry)
    latest_estimates: dict[str, SubjectEstimate] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._store = Store[dict](self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry_id}")

    async def async_initialize(self) -> None:
        """Load stored mappings and populate runtime state."""

        stored = await self._store.async_load()
        self.subject_registry = SubjectRegistry.from_dict(stored.get("links") if stored else None)
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Refresh discovery, hydrate mappings, and rebuild estimates."""

        previous_subjects = set(self.subject_registry.subjects())
        self.discovered_sources = await async_discover_sources(self.hass)
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

    async def async_clear_subject(self, subject_id: str) -> None:
        """Remove all data for one subject."""

        previous_subjects = set(self.subject_registry.subjects())
        self.subject_registry.clear_subject(subject_id)
        self.latest_estimates.pop(subject_id, None)
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

    def _rebuild_estimates_from_discovery(self) -> None:
        self.subject_registry.clear_fixes()
        latest_estimates: dict[str, SubjectEstimate] = {}

        for subject_id in self.subject_registry.subjects():
            for link in self.subject_registry.links_for_subject(subject_id):
                state = self.hass.states.get(link.source_id)
                attributes = state.attributes if state is not None else {}
                fix = extract_location_fix(link.source_id, attributes)
                if fix is None:
                    continue
                latest_estimates[subject_id] = self.subject_registry.ingest_fix(
                    subject_id, link.source_id, fix
                )

        self.latest_estimates = {
            subject_id: self._enrich_estimate(estimate)
            for subject_id, estimate in latest_estimates.items()
        }

    def _enrich_estimate(self, estimate: SubjectEstimate) -> SubjectEstimate:
        home_latitude = getattr(self.hass.config, ATTR_LATITUDE, None)
        home_longitude = getattr(self.hass.config, ATTR_LONGITUDE, None)
        if home_latitude is None or home_longitude is None:
            return estimate

        estimate.distance_from_home_m = round(
            distance_m(home_latitude, home_longitude, estimate.latitude, estimate.longitude), 1
        )
        estimate.bearing_from_home_deg = round(
            bearing_deg(home_latitude, home_longitude, estimate.latitude, estimate.longitude), 1
        )
        estimate.direction_from_home = cardinal_direction(estimate.bearing_from_home_deg)
        return estimate

    async def _async_save(self) -> None:
        await self._store.async_save({"links": self.subject_registry.as_dict()})

    def _async_dispatch(self, previous_subjects: set[str]) -> None:
        async_dispatcher_send(self.hass, update_signal(self.entry_id))
        current_subjects = set(self.subject_registry.subjects())
        if current_subjects != previous_subjects:
            async_dispatcher_send(self.hass, subjects_signal(self.entry_id))
