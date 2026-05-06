"""Subject/source mapping and in-memory fix registry."""

from __future__ import annotations

from collections import defaultdict

from .fusion import fuse_subject
from .models import LocationFix, SourceLink, SubjectEstimate


class SubjectRegistry:
    """Maintain subject/source links and recent fixes."""

    def __init__(self) -> None:
        self._links: dict[str, dict[str, SourceLink]] = defaultdict(dict)
        self._fixes: dict[str, dict[str, LocationFix]] = defaultdict(dict)

    def link_source(self, subject_id: str, source_id: str, source_name: str) -> None:
        """Link a source to a subject."""

        self._links[subject_id][source_id] = SourceLink(
            subject_id=subject_id,
            source_id=source_id,
            source_name=source_name,
        )

    def ingest_fix(
        self, subject_id: str, source_id: str, fix: LocationFix
    ) -> SubjectEstimate:
        """Store a fix and return an updated estimate."""

        self._fixes[subject_id][source_id] = fix
        return fuse_subject(subject_id, list(self._fixes[subject_id].values()))

    def source_count(self, subject_id: str) -> int:
        """Return the number of linked sources for a subject."""

        return len(self._links[subject_id])

    def subjects(self) -> list[str]:
        """Return the known subjects."""

        return sorted(set(self._links) | set(self._fixes))

