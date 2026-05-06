"""Confidence scoring helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import LocationFix


def confidence_label(score: float) -> str:
    """Return a stable label for a normalized confidence score."""

    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.3:
        return "low"
    return "unknown"


def score_fix_recency(fix: LocationFix) -> float:
    """Score fix freshness conservatively."""

    age_seconds = max((datetime.now(UTC) - fix.observed_at).total_seconds(), 0)
    if age_seconds <= 30:
        return 1.0
    if age_seconds <= 300:
        return 0.8
    if age_seconds <= 1800:
        return 0.55
    if age_seconds <= 7200:
        return 0.3
    return 0.1

