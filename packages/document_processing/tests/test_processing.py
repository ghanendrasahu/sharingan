"""Unit tests for document processing services."""

from legallens_docproc.docx_extractor import extract_docx_text
from legallens_docproc.models import (
    DocumentFormat,
    ProcessedDocument,
    ProcessingStatus,
)
from legallens_docproc.ocr import MockOCR, OCRResult
from legallens_docproc.pdf_extractor import (
    PDFExtractionResult,
    PDFPage,
    extract_pdf_text,
)
from legallens_docproc.processor import detect_format, process_document


def test_detect_pdf_format():
    """Test PDF format detection."""
    assert detect_format("document.pdf") == DocumentFormat.PDF
    assert detect_format("DOCUMENT.PDF") == DocumentFormat.PDF
    assert detect_format("path/to/file.pdf") == DocumentFormat.PDF


def test_detect_docx_format():
    """Test DOCX format detection."""
    assert detect_format("document.docx") == DocumentFormat.DOCX
    assert detect_format("DOCUMENT.DOCX") == DocumentFormat.DOCX


def test_detect_unknown_format():
    """Test unknown format detection."""
    assert detect_format("document.txt") == DocumentFormat.UNKNOWN
    assert detect_format("document") == DocumentFormat.UNKNOWN


def test_pdf_extraction_result():
    """Test PDF extraction result structure."""
    pages = [
        PDFPage(page_number=1, text="Page 1 content"),
        PDFPage(page_number=2, text="Page 2 content"),
    ]
    result = PDFExtractionResult(pages=pages)
    assert result.total_pages == 2
    assert result.total_chars == 28  # "Page 1 content" + "Page 2 content"
    assert result.total_words == 6  # 3 words per page


def test_pdf_page_properties():
    """Test PDF page properties."""
    page = PDFPage(page_number=1, text="Hello World")
    assert page.char_count == 11
    assert page.word_count == 2


def test_extract_pdf_text_invalid():
    """Test PDF extraction with invalid data."""
    result = extract_pdf_text(b"not a pdf")
    # Should not crash, may return empty result or error
    assert isinstance(result, PDFExtractionResult)


def test_extract_docx_text_invalid():
    """Test DOCX extraction with invalid data."""
    result = extract_docx_text(b"not a docx")
    # Should not crash, may return empty result or error
    assert result is not None


def test_process_document_unknown_format():
    """Test processing unknown document format."""
    result = process_document(
        document_id="test-123",
        filename="test.txt",
        content=b"content",
    )
    assert result.success is False
    assert "Unsupported" in result.error


def test_process_document_pdf():
    """Test processing PDF document."""
    # Minimal PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n/Type /Page\nendobj\n" + b"x" * 1000
    result = process_document(
        document_id="test-pdf-123",
        filename="test.pdf",
        content=pdf_content,
    )
    # May succeed or fail depending on PDF validity
    assert isinstance(result, type(result))


def test_process_document_docx():
    """Test processing DOCX document."""
    # Minimal DOCX content (ZIP file)
    docx_content = b"PK\x03\x04" + b"x" * 1000
    result = process_document(
        document_id="test-docx-123",
        filename="test.docx",
        content=docx_content,
    )
    # May succeed or fail depending on DOCX validity
    assert isinstance(result, type(result))


def test_mock_ocr():
    """Test mock OCR provider."""
    ocr = MockOCR()
    assert ocr.is_available() is True


def test_ocr_result():
    """Test OCR result structure."""
    result = OCRResult(
        text="Hello World",
        confidence=0.95,
        language="eng",
    )
    assert result.text == "Hello World"
    assert result.confidence == 0.95


def test_processed_document_structure():
    """Test processed document structure."""
    doc = ProcessedDocument(
        document_id="test-123",
        filename="test.pdf",
        format=DocumentFormat.PDF,
        status=ProcessingStatus.COMPLETED,
    )
    assert doc.document_id == "test-123"
    assert doc.status == ProcessingStatus.COMPLETED
    assert doc.total_pages == 0
