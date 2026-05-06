"""Subject/source mapping and in-memory fix registry."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .fusion import fuse_subject
from .models import LocationFix, SourceLink, SubjectEstimate


class SubjectRegistry:
    """Maintain subject/source links and recent fixes."""

    def __init__(self) -> None:
        self._links: dict[str, dict[str, SourceLink]] = defaultdict(dict)
        self._fixes: dict[str, dict[str, LocationFix]] = defaultdict(dict)

    def link_source(
        self,
        subject_id: str,
        source_id: str,
        source_name: str,
        source_type: str = "unknown",
    ) -> None:
        """Link a source to a subject."""

        self._links[subject_id][source_id] = SourceLink(
            subject_id=subject_id,
            source_id=source_id,
            source_name=source_name,
            source_type=source_type,
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

    def links_for_subject(self, subject_id: str) -> list[SourceLink]:
        """Return links for one subject."""

        return sorted(self._links[subject_id].values(), key=lambda link: link.source_id)

    def iter_links(self) -> Iterable[SourceLink]:
        """Yield all source links."""

        for source_links in self._links.values():
            yield from source_links.values()

    def estimate_for_subject(self, subject_id: str) -> SubjectEstimate | None:
        """Return a current estimate if this subject has valid fixes."""

        fixes = list(self._fixes[subject_id].values())
        if not fixes:
            return None
        return fuse_subject(subject_id, fixes)

    def clear_subject(self, subject_id: str) -> None:
        """Remove links and fixes for a subject."""

        self._links.pop(subject_id, None)
        self._fixes.pop(subject_id, None)

    def clear_fixes(self) -> None:
        """Drop transient fix state while preserving mappings."""

        self._fixes.clear()

    def as_dict(self) -> dict[str, list[dict[str, str]]]:
        """Serialize source links for storage."""

        return {
            subject_id: [
                {
                    "subject_id": link.subject_id,
                    "source_id": link.source_id,
                    "source_name": link.source_name,
                    "source_type": link.source_type,
                }
                for link in self.links_for_subject(subject_id)
            ]
            for subject_id in self.subjects()
            if self._links.get(subject_id)
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[dict[str, str]]] | None) -> SubjectRegistry:
        """Restore a registry from stored mappings."""

        registry = cls()
        if not data:
            return registry

        for subject_id, links in data.items():
            for link in links:
                registry.link_source(
                    subject_id=subject_id,
                    source_id=link["source_id"],
                    source_name=link.get("source_name", link["source_id"]),
                    source_type=link.get("source_type", "unknown"),
                )
        return registry
