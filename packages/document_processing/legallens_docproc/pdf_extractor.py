"""PDF text extraction service."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PDFPage:
    """A single page from a PDF."""

    page_number: int
    text: str
    char_count: int = 0
    word_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)
        self.word_count = len(self.text.split()) if self.text else 0


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""

    pages: list[PDFPage] = field(default_factory=list)
    total_pages: int = 0
    total_chars: int = 0
    total_words: int = 0
    metadata: dict = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self):
        self.total_pages = len(self.pages)
        self.total_chars = sum(p.char_count for p in self.pages)
        self.total_words = sum(p.word_count for p in self.pages)


def extract_pdf_text(pdf_data: bytes) -> PDFExtractionResult:
    """Extract text from PDF using PyMuPDF.

    Falls back to basic extraction if PyMuPDF fails.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_data, filetype="pdf")
        pages = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            pages.append(
                PDFPage(
                    page_number=page_num + 1,
                    text=text,
                )
            )

        metadata = doc.metadata or {}
        doc.close()

        return PDFExtractionResult(
            pages=pages,
            metadata={
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
            },
        )
    except ImportError:
        return PDFExtractionResult(error="PyMuPDF not installed. Install with: pip install pymupdf")
    except Exception as e:
        return PDFExtractionResult(error=f"PDF extraction failed: {e!s}")


def extract_pdf_text_fallback(pdf_data: bytes) -> PDFExtractionResult:
    """Basic PDF text extraction without external dependencies.

    This is a minimal fallback that extracts readable text.
    """
    try:
        import re

        # Simple extraction - find text between stream markers
        text = pdf_data.decode("latin-1", errors="ignore")

        # Extract text from BT/ET blocks
        pages = []
        page_texts = re.findall(r"BT\s*(.*?)\s*ET", text, re.DOTALL)

        for i, page_text in enumerate(page_texts):
            # Extract text from Tj/TJ operators
            text_parts = re.findall(r"\((.*?)\)", page_text)
            page_text_cleaned = " ".join(text_parts)

            if page_text_cleaned.strip():
                pages.append(
                    PDFPage(
                        page_number=i + 1,
                        text=page_text_cleaned,
                    )
                )

        return PDFExtractionResult(pages=pages)
    except Exception:
        return PDFExtractionResult(error="Fallback extraction failed")
