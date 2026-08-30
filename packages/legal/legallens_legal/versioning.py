"""Legal source versioning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceVersion:
    """Tracks versions of legal sources."""

    source_id: str
    version: str
    effective_date: str
    is_current: bool = True
    notes: str = ""


# Registry of source versions
VERSIONS: dict[str, list[SourceVersion]] = {
    "indian_contract_act_1872": [
        SourceVersion(
            source_id="indian_contract_act_1872",
            version="1.0",
            effective_date="1872-04-25",
            is_current=True,
            notes="Original enactment",
        ),
        SourceVersion(
            source_id="indian_contract_act_1872",
            version="1.1",
            effective_date="2023-01-01",
            is_current=True,
            notes="Amended by various notifications",
        ),
    ],
    "companies_act_2013": [
        SourceVersion(
            source_id="companies_act_2013",
            version="1.0",
            effective_date="2013-09-12",
            is_current=True,
            notes="Original enactment",
        ),
        SourceVersion(
            source_id="companies_act_2013",
            version="1.1",
            effective_date="2024-01-01",
            is_current=True,
            notes="Amended by Companies Amendment Act, 2023",
        ),
    ],
    "it_act_2000": [
        SourceVersion(
            source_id="it_act_2000",
            version="1.0",
            effective_date="2000-10-17",
            is_current=True,
            notes="Original enactment",
        ),
        SourceVersion(
            source_id="it_act_2000",
            version="2.0",
            effective_date="2009-02-05",
            is_current=True,
            notes="Amended by IT Amendment Act, 2008",
        ),
    ],
}


def get_current_version(source_id: str) -> SourceVersion | None:
    """Get the current version of a legal source."""
    versions = VERSIONS.get(source_id, [])
    for v in versions:
        if v.is_current:
            return v
    return versions[-1] if versions else None


def get_version_history(source_id: str) -> list[SourceVersion]:
    """Get version history for a source."""
    return VERSIONS.get(source_id, [])
