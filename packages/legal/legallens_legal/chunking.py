"""Legal text chunking."""

from __future__ import annotations

import hashlib

from legallens_legal.models import LegalChunk, LegalSection


def chunk_section(section: LegalSection) -> list[LegalChunk]:
    """Chunk a legal section into retrievable chunks."""
    content = section.content
    if not content:
        return []

    chunk_id = f"chunk_{hashlib.sha256(f'{section.source_id}:{section.section_number}'.encode()).hexdigest()[:12]}"

    return [
        LegalChunk(
            chunk_id=chunk_id,
            source_id=section.source_id,
            section_number=section.section_number,
            title=section.title,
            content=content,
            chunk_index=0,
            char_start=0,
            char_end=len(content),
            metadata={
                "is_definitions": section.is_definitions,
                "parent_section": section.parent_section,
            },
        )
    ]


def chunk_text(text: str, max_words: int = 500) -> list[dict]:
    """Chunk arbitrary text into smaller pieces."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk_words = words[i : i + max_words]
        chunks.append(
            {
                "text": " ".join(chunk_words),
                "index": i // max_words,
                "word_count": len(chunk_words),
            }
        )

    return chunks
