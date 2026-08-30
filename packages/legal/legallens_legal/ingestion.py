"""Legal corpus ingestion."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from legallens_legal.models import LegalSection, LegalSource


def load_source(source_id: str) -> tuple[LegalSource | None, list[LegalSection]]:
    """Load a legal source by ID."""
    from legallens_legal.sources import ALL_SECTIONS, ALL_SOURCES

    source = next((s for s in ALL_SOURCES if s.source_id == source_id), None)
    sections = [s for s in ALL_SECTIONS if s.source_id == source_id]

    return source, sections


def load_all_sources() -> list[tuple[LegalSource, list[LegalSection]]]:
    """Load all available legal sources."""
    from legallens_legal.sources import ALL_SECTIONS, ALL_SOURCES

    results = []
    for source in ALL_SOURCES:
        sections = [s for s in ALL_SECTIONS if s.source_id == source.source_id]
        results.append((source, sections))

    return results


def search_sections(query: str, source_id: str | None = None) -> list[LegalSection]:
    """Search sections by keyword."""
    from legallens_legal.sources import ALL_SECTIONS

    query_lower = query.lower()
    results = []

    for section in ALL_SECTIONS:
        if source_id and section.source_id != source_id:
            continue

        if (
            query_lower in section.title.lower()
            or query_lower in section.content.lower()
            or query_lower in section.section_number
        ):
            results.append(section)

    return results
