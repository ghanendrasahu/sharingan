"""Legal source and chunk models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class LegalSource:
    """A legal source (act, regulation, etc.)."""

    source_id: str
    name: str
    short_name: str
    year: int
    jurisdiction: str = "India"
    status: str = "active"  # active, amended, repealed
    description: str = ""
    url: str | None = None
    version: str = "1.0"
    last_updated: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now(tz=UTC).isoformat()


@dataclass
class LegalSection:
    """A section within a legal source."""

    section_id: str
    source_id: str
    section_number: str
    title: str
    content: str
    parent_section: str | None = None
    is_definitions: bool = False

    @property
    def full_reference(self) -> str:
        """Get full reference like 'Section 27, Indian Contract Act, 1872'."""
        return f"Section {self.section_number}, {self.source_id}"


@dataclass
class LegalChunk:
    """A chunk of legal text for retrieval."""

    chunk_id: str
    source_id: str
    section_number: str
    title: str
    content: str
    chunk_index: int = 0
    char_start: int = 0
    char_end: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.char_end:
            self.char_end = self.char_start + len(self.content)

    @property
    def word_count(self) -> int:
        """Count words in chunk."""
        return len(self.content.split()) if self.content else 0
