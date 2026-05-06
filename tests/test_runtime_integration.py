from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.location_intelligence.const import DEFAULT_ENTRY_NAME, DOMAIN


async def _async_setup_integration(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_ENTRY_NAME,
        data={},
        entry_id="test-entry",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _sensor_entity_id(hass: HomeAssistant, unique_id: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


async def test_config_entry_setup_creates_subject_sensors(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    hass.config.latitude = 48.2082
    hass.config.longitude = 16.3738

    hass.states.async_set(
        "person.alice",
        "home",
        {
            "friendly_name": "Alice",
            "latitude": 48.2083,
            "longitude": 16.3739,
            "source": "device_tracker.alice_phone",
        },
    )
    hass.states.async_set(
        "device_tracker.alice_phone",
        "home",
        {
            "friendly_name": "Alice Phone",
            "latitude": 48.20835,
            "longitude": 16.37395,
            "gps_accuracy": 12,
            "source_type": "gps",
        },
    )

    entry = await _async_setup_integration(hass)
    runtime = entry.runtime_data

    assert runtime.subject_registry.subjects() == ["person.alice"]
    assert "person.alice" in runtime.latest_estimates

    discovered_sources = hass.states.get(
        _sensor_entity_id(hass, "location_intelligence_discovered_sources")
    )
    tracked_subjects = hass.states.get(
        _sensor_entity_id(hass, "location_intelligence_tracked_subjects")
    )
    status = hass.states.get(
        _sensor_entity_id(hass, "location_intelligence_person.alice_status")
    )
    reference_place = hass.states.get(
        _sensor_entity_id(hass, "location_intelligence_person.alice_reference_place")
    )
    distance_from_home = hass.states.get(
        _sensor_entity_id(hass, "location_intelligence_person.alice_distance_from_home")
    )

    assert discovered_sources is not None
    assert int(discovered_sources.state) >= 2
    assert discovered_sources.attributes["sources"] == sorted(runtime.discovered_sources)
    assert tracked_subjects is not None
    assert tracked_subjects.state == "1"
    assert status is not None
    assert status.state in {"low", "medium", "high"}
    assert reference_place is not None
    assert reference_place.state == "Home"
    assert distance_from_home is not None
    assert float(distance_from_home.state) >= 0.0


async def test_services_manage_subjects_and_reference_places(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    hass.config.latitude = 48.2082
    hass.config.longitude = 16.3738

    entry = await _async_setup_integration(hass)

    await hass.services.async_call(
        DOMAIN,
        "ingest_fix",
        {
            "subject_id": "person.bob",
            "source_id": "manual.bob_phone",
            "source_name": "Bob Phone",
            "latitude": 48.21,
            "longitude": 16.38,
            "accuracy_m": 8,
            "confidence": 0.9,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    status_entity_id = _sensor_entity_id(hass, "location_intelligence_person.bob_status")
    reference_entity_id = _sensor_entity_id(
        hass, "location_intelligence_person.bob_reference_place"
    )

    assert "person.bob" in entry.runtime_data.latest_estimates
    assert hass.states.get(status_entity_id) is not None
    assert hass.states.get(reference_entity_id).state == "Home"

    await hass.services.async_call(
        DOMAIN,
        "upsert_place",
        {
            "place_id": "office",
            "place_name": "Office",
            "kind": "coordinates",
            "latitude": 48.22,
            "longitude": 16.4,
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "assign_reference_place",
        {"subject_id": "person.bob", "place_id": "office"},
        blocking=True,
    )
    await hass.async_block_till_done()

    estimate = entry.runtime_data.latest_estimates["person.bob"]
    assert estimate.reference_place_id == "office"
    assert estimate.reference_place_name == "Office"
    assert hass.states.get(reference_entity_id).state == "Office"

    await hass.services.async_call(
        DOMAIN,
        "clear_subject",
        {"subject_id": "person.bob"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert "person.bob" not in entry.runtime_data.latest_estimates
    assert hass.states.get(status_entity_id).state == STATE_UNAVAILABLE


async def test_exclude_and_include_person_entity_refreshes_subjects(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    hass.config.latitude = 48.2082
    hass.config.longitude = 16.3738

    hass.states.async_set(
        "person.charlie",
        "home",
        {
            "friendly_name": "Charlie",
            "latitude": 48.205,
            "longitude": 16.36,
        },
    )

    entry = await _async_setup_integration(hass)
    tracked_subjects_entity_id = _sensor_entity_id(
        hass, "location_intelligence_tracked_subjects"
    )

    assert entry.runtime_data.subject_registry.subjects() == ["person.charlie"]
    assert hass.states.get(tracked_subjects_entity_id).state == "1"

    await hass.services.async_call(
        DOMAIN,
        "exclude_person_entity",
        {"entity_id": "person.charlie"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert entry.runtime_data.subject_registry.subjects() == []
    assert "person.charlie" in entry.runtime_data.excluded_person_entities
    assert hass.states.get(tracked_subjects_entity_id).state == "0"

    await hass.services.async_call(
        DOMAIN,
        "include_person_entity",
        {"entity_id": "person.charlie"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert entry.runtime_data.subject_registry.subjects() == ["person.charlie"]
    assert "person.charlie" not in entry.runtime_data.excluded_person_entities
    assert hass.states.get(tracked_subjects_entity_id).state == "1"
