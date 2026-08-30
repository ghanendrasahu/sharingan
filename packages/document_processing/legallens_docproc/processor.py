"""Document processing pipeline."""

from __future__ import annotations

import time
from pathlib import Path

from .docx_extractor import extract_docx_text
from .models import (
    DocumentFormat,
    PageContent,
    ProcessedDocument,
    ProcessingResult,
    ProcessingStatus,
    TextBlock,
)
from .pdf_extractor import extract_pdf_text


def detect_format(filename: str) -> DocumentFormat:
    """Detect document format from filename."""
    ext = Path(filename).suffix.lower()
    format_map = {
        ".pdf": DocumentFormat.PDF,
        ".docx": DocumentFormat.DOCX,
    }
    return format_map.get(ext, DocumentFormat.UNKNOWN)


def process_document(
    document_id: str,
    filename: str,
    content: bytes,
) -> ProcessingResult:
    """Process a document through the extraction pipeline.

    Steps:
    1. Detect format
    2. Extract text
    3. Build structured representation
    """
    start_time = time.time()

    try:
        # Detect format
        doc_format = detect_format(filename)
        if doc_format == DocumentFormat.UNKNOWN:
            return ProcessingResult(
                success=False,
                error=f"Unsupported document format: {filename}",
            )

        # Create document structure
        doc = ProcessedDocument(
            document_id=document_id,
            filename=filename,
            format=doc_format,
            status=ProcessingStatus.EXTRACTING,
        )

        # Extract text based on format
        if doc_format == DocumentFormat.PDF:
            pdf_result = extract_pdf_text(content)
            if pdf_result.error:
                return ProcessingResult(
                    success=False,
                    error=pdf_result.error,
                )

            # Convert to structured pages
            pages = []
            for page_data in pdf_result.pages:
                text_blocks = [
                    TextBlock(
                        text=page_data.text,
                        page_number=page_data.page_number,
                        block_index=0,
                    )
                ]
                pages.append(
                    PageContent(
                        page_number=page_data.page_number,
                        text=page_data.text,
                        text_blocks=text_blocks,
                    )
                )

            doc.pages = pages
            doc.metadata = pdf_result.metadata

        elif doc_format == DocumentFormat.DOCX:
            docx_result = extract_docx_text(content)
            if docx_result.error:
                return ProcessingResult(
                    success=False,
                    error=docx_result.error,
                )

            # Convert paragraphs to pages (single page for DOCX)
            full_text = "\n\n".join(p.text for p in docx_result.paragraphs if p.text)
            text_blocks = [
                TextBlock(
                    text=p.text,
                    page_number=1,
                    block_index=p.index,
                    is_heading=p.is_heading,
                    heading_level=p.heading_level,
                )
                for p in docx_result.paragraphs
                if p.text.strip()
            ]

            doc.pages = [
                PageContent(
                    page_number=1,
                    text=full_text,
                    text_blocks=text_blocks,
                )
            ]
            doc.metadata = docx_result.metadata

        # Mark as completed
        doc.status = ProcessingStatus.COMPLETED
        doc.processing_time_ms = (time.time() - start_time) * 1000

        return ProcessingResult(
            success=True,
            document=doc,
        )

    except Exception as e:
        return ProcessingResult(
            success=False,
            error=f"Processing failed: {e!s}",
        )


async def process_document_async(
    document_id: str,
    filename: str,
    content: bytes,
) -> ProcessingResult:
    """Async wrapper for document processing."""
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        process_document,
        document_id,
        filename,
        content,
    )
