from custom_components.location_intelligence.subject_mapping import SubjectRegistry


def test_subject_registry_round_trips_links() -> None:
    registry = SubjectRegistry()
    registry.link_source("person.alice", "person.alice", "Alice", "person")
    registry.link_source(
        "person.alice",
        "device_tracker.alice_phone",
        "Alice Phone",
        "device_tracker",
    )

    restored = SubjectRegistry.from_dict(registry.as_dict())

    assert restored.subjects() == ["person.alice"]
    links = restored.links_for_subject("person.alice")
    assert [link.source_id for link in links] == [
        "device_tracker.alice_phone",
        "person.alice",
    ]
    assert links[0].source_type == "device_tracker"

