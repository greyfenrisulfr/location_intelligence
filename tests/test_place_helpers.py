from datetime import UTC, datetime, timedelta

from custom_components.location_intelligence.models import (
    LocationFix,
    ReferencePlace,
    SubjectEstimate,
)
from custom_components.location_intelligence.place_helpers import (
    latest_recent_fix,
    remember_recent_fix,
    resolve_reference_place,
)


def test_resolve_reference_place_uses_dynamic_subject_place() -> None:
    estimate = SubjectEstimate(
        subject_id="person.leader",
        latitude=48.2,
        longitude=16.37,
        confidence=0.8,
        confidence_label="high",
        source_count=1,
        rationale=[],
    )

    resolved = resolve_reference_place(
        subject_id="person.follower",
        subject_reference_places={"person.follower": "leader_place"},
        places={
            "leader_place": ReferencePlace(
                place_id="leader_place",
                name="Group Leader",
                kind="subject",
                target_subject_id="person.leader",
            )
        },
        latest_estimates={"person.leader": estimate},
        recent_fixes={},
        home_coordinates=(48.1, 16.3),
    )

    assert resolved is not None
    assert resolved.name == "Group Leader"
    assert resolved.kind == "subject"
    assert resolved.latitude == 48.2


def test_resolve_reference_place_uses_last_known_fix() -> None:
    recent_fixes: dict[str, dict[str, list[LocationFix]]] = {}
    remember_recent_fix(
        recent_fixes,
        "person.dog",
        "collar",
        LocationFix(
            latitude=48.25,
            longitude=16.4,
            observed_at=datetime.now(UTC) - timedelta(minutes=5),
        ),
        limit=5,
    )

    resolved = resolve_reference_place(
        subject_id="person.owner",
        subject_reference_places={"person.owner": "dog_last_known"},
        places={
            "dog_last_known": ReferencePlace(
                place_id="dog_last_known",
                name="Dog Last Known",
                kind="last_known",
                target_subject_id="person.dog",
            )
        },
        latest_estimates={},
        recent_fixes=recent_fixes,
        home_coordinates=(48.1, 16.3),
    )

    assert resolved is not None
    assert resolved.kind == "last_known"
    assert resolved.longitude == 16.4


def test_recent_fix_history_is_bounded() -> None:
    recent_fixes: dict[str, dict[str, list[LocationFix]]] = {}
    base_time = datetime.now(UTC)

    for index in range(7):
        remember_recent_fix(
            recent_fixes,
            "person.alice",
            "phone",
            LocationFix(
                latitude=48.2 + index,
                longitude=16.3,
                observed_at=base_time + timedelta(seconds=index),
            ),
            limit=5,
        )

    latest = latest_recent_fix(recent_fixes, "person.alice", "phone")

    assert latest is not None
    assert len(recent_fixes["person.alice"]["phone"]) == 5
    assert latest.latitude == 54.2
