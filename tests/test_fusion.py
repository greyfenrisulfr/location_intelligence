from custom_components.location_intelligence.fusion import fuse_subject
from custom_components.location_intelligence.models import LocationFix


def test_fuse_subject_returns_conservative_estimate() -> None:
    estimate = fuse_subject(
        "alice",
        [
            LocationFix(latitude=48.2082, longitude=16.3738, accuracy_m=15, confidence=0.9),
            LocationFix(latitude=48.2083, longitude=16.3737, accuracy_m=20, confidence=0.8),
        ],
    )

    assert estimate.subject_id == "alice"
    assert estimate.source_count == 2
    assert 0.1 <= estimate.confidence <= 0.95
    assert estimate.confidence_label in {"low", "medium", "high"}
