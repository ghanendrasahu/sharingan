"""Structured document representation for processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DocumentFormat(StrEnum):
    """Document format types."""

    PDF = "pdf"
    DOCX = "docx"
    UNKNOWN = "unknown"


class ProcessingStatus(StrEnum):
    """Document processing status."""

    PENDING = "pending"
    EXTRACTING = "extracting"
    SEGMENTING = "segmenting"
    CLASSIFYING = "classifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TextBlock:
    """A block of text with position information."""

    text: str
    page_number: int
    block_index: int = 0
    char_start: int = 0
    char_end: int = 0
    is_heading: bool = False
    heading_level: int | None = None

    def __post_init__(self):
        self.char_end = self.char_start + len(self.text)


@dataclass
class ProcessedDocument:
    """Structured representation of a processed document."""

    document_id: str
    filename: str
    format: DocumentFormat
    status: ProcessingStatus = ProcessingStatus.PENDING

    # Extracted content
    pages: list[PageContent] = field(default_factory=list)
    full_text: str = ""

    # Metadata
    total_pages: int = 0
    total_chars: int = 0
    total_words: int = 0
    metadata: dict = field(default_factory=dict)

    # Processing info
    processing_time_ms: float | None = None
    error: str | None = None

    def __post_init__(self):
        self.full_text = "\n\n".join(page.text for page in self.pages if page.text)
        self.total_pages = len(self.pages)
        self.total_chars = len(self.full_text)
        self.total_words = len(self.full_text.split()) if self.full_text else 0


@dataclass
class PageContent:
    """Content of a single page."""

    page_number: int
    text: str
    text_blocks: list[TextBlock] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    has_images: bool = False
    is_scanned: bool = False

    def __post_init__(self):
        self.char_count = len(self.text)
        self.word_count = len(self.text.split()) if self.text else 0


@dataclass
class ProcessingResult:
    """Result of document processing."""

    success: bool
    document: ProcessedDocument | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
