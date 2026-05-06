"""Location fusion logic."""

from __future__ import annotations

from statistics import mean

from .calculations import distance_m
from .confidence import confidence_label, score_fix_recency
from .models import LocationFix, SubjectEstimate


def fuse_subject(subject_id: str, fixes: list[LocationFix]) -> SubjectEstimate:
    """Fuse multiple fixes into a conservative estimate."""

    weighted = [(fix, fix.normalized_weight() * score_fix_recency(fix)) for fix in fixes]
    weighted = [(fix, weight) for fix, weight in weighted if weight > 0]
    if not weighted:
        raise ValueError("Cannot fuse subject without valid fixes")

    total_weight = sum(weight for _, weight in weighted)
    latitude = sum(fix.latitude * weight for fix, weight in weighted) / total_weight
    longitude = sum(fix.longitude * weight for fix, weight in weighted) / total_weight

    dispersion = mean(
        distance_m(latitude, longitude, fix.latitude, fix.longitude) for fix, _ in weighted
    )
    average_accuracy = _mean_defined([fix.accuracy_m for fix, _ in weighted])
    source_count = len(weighted)

    confidence = min(
        0.95,
        max(
            0.1,
            (total_weight / source_count)
            * _diversity_bonus(source_count)
            * _dispersion_penalty(dispersion),
        ),
    )

    rationale = [
        f"fused {source_count} source(s)",
        f"mean dispersion {dispersion:.1f}m",
        f"confidence bounded to avoid false precision",
    ]

    return SubjectEstimate(
        subject_id=subject_id,
        latitude=latitude,
        longitude=longitude,
        confidence=round(confidence, 3),
        confidence_label=confidence_label(confidence),
        source_count=source_count,
        rationale=rationale,
        accuracy_m=average_accuracy,
        observed_at=max(fix.observed_at for fix, _ in weighted),
    )


def _diversity_bonus(source_count: int) -> float:
    if source_count <= 1:
        return 0.75
    if source_count == 2:
        return 0.9
    return 1.0


def _dispersion_penalty(dispersion_m: float) -> float:
    if dispersion_m <= 25:
        return 1.0
    if dispersion_m <= 100:
        return 0.75
    if dispersion_m <= 500:
        return 0.45
    return 0.2


def _mean_defined(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return mean(filtered)

