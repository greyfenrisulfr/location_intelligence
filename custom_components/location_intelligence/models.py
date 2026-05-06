"""Core models for Location Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite


@dataclass(slots=True)
class LocationFix:
    """A single location observation from one source."""

    latitude: float
    longitude: float
    accuracy_m: float | None = None
    confidence: float | None = None
    speed_m_s: float | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def normalized_weight(self) -> float:
        """Return a conservative fusion weight for the fix."""

        if not isfinite(self.latitude) or not isfinite(self.longitude):
            return 0.0

        confidence = min(max(self.confidence or 0.5, 0.0), 1.0)
        if self.accuracy_m is None or self.accuracy_m <= 0:
            return confidence
        return confidence * max(0.05, min(1.0, 50 / self.accuracy_m))


@dataclass(slots=True)
class SourceLink:
    """Mapping between a logical subject and a concrete source."""

    subject_id: str
    source_id: str
    source_name: str
    source_type: str = "unknown"


@dataclass(slots=True)
class ReferencePlace:
    """A named place that can be static or dynamically resolved."""

    place_id: str
    name: str
    kind: str = "coordinates"
    latitude: float | None = None
    longitude: float | None = None
    target_subject_id: str | None = None


@dataclass(slots=True)
class ResolvedPlace:
    """A reference place with concrete coordinates."""

    place_id: str
    name: str
    kind: str
    latitude: float
    longitude: float


@dataclass(slots=True)
class SubjectEstimate:
    """Derived position estimate for a subject."""

    subject_id: str
    latitude: float
    longitude: float
    confidence: float
    confidence_label: str
    source_count: int
    rationale: list[str]
    accuracy_m: float | None = None
    reference_place_id: str | None = None
    reference_place_name: str | None = None
    reference_place_kind: str | None = None
    distance_from_reference_m: float | None = None
    bearing_from_reference_deg: float | None = None
    direction_from_reference: str | None = None
    distance_from_home_m: float | None = None
    bearing_from_home_deg: float | None = None
    direction_from_home: str | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
