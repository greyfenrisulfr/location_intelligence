from custom_components.location_intelligence.location_helpers import extract_location_fix


def test_extract_location_fix_from_attributes() -> None:
    fix = extract_location_fix(
        "device_tracker.alice_phone",
        {
            "latitude": 48.2082,
            "longitude": 16.3738,
            "gps_accuracy": 12,
            "speed": 1.5,
            "source_type": "gps",
        },
    )

    assert fix is not None
    assert fix.latitude == 48.2082
    assert fix.longitude == 16.3738
    assert fix.accuracy_m == 12
    assert fix.confidence == 0.85
