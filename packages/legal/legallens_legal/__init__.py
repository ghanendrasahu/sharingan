"""LegalLens Legal - Versioned Indian legal corpus."""

from legallens_legal.chunking import chunk_section, chunk_text
from legallens_legal.ingestion import load_all_sources, load_source, search_sections
from legallens_legal.models import LegalChunk, LegalSection, LegalSource
from legallens_legal.versioning import get_current_version, get_version_history

__all__ = [
    "LegalChunk",
    "LegalSection",
    "LegalSource",
    "chunk_section",
    "chunk_text",
    "get_current_version",
    "get_version_history",
    "load_all_sources",
    "load_source",
    "search_sections",
]
