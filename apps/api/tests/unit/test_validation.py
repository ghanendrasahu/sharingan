"""Unit tests for document validation services."""

import pytest

from app.services.validation import (
    DocumentValidationError,
    detect_file_type,
    get_pdf_page_count,
    validate_document,
    validate_file_signature,
    validate_file_size,
)

# Minimal valid PDF header
PDF_HEADER = b"%PDF-1.4\n"
# Minimal valid DOCX header (ZIP file)
DOCX_HEADER = b"PK\x03\x04\x14\x00\x06\x00\x08\x00"


def test_validate_pdf_signature():
    """Test PDF signature validation."""
    assert validate_file_signature(PDF_HEADER + b"rest of content", "pdf") is True
    assert validate_file_signature(b"Not a PDF", "pdf") is False


def test_validate_docx_signature():
    """Test DOCX signature validation."""
    assert validate_file_signature(DOCX_HEADER + b"rest of content", "docx") is True
    assert validate_file_signature(b"Not a DOCX", "docx") is False


def test_validate_file_too_small():
    """Test file too small validation."""
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_file_size(b"tiny", ".pdf")
    assert exc_info.value.code == "FILE_TOO_SMALL"


def test_validate_file_too_large():
    """Test file too large validation."""
    large_data = b"x" * (51 * 1024 * 1024)  # 51MB
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_file_size(large_data, ".pdf")
    assert exc_info.value.code == "FILE_TOO_LARGE"


def test_validate_file_valid_size():
    """Test valid file size passes."""
    valid_data = b"x" * (1024)  # 1KB
    validate_file_size(valid_data, ".pdf")  # Should not raise


def test_detect_pdf_type():
    """Test PDF type detection."""
    assert detect_file_type(PDF_HEADER + b"content") == "pdf"


def test_detect_docx_type():
    """Test DOCX type detection."""
    assert detect_file_type(DOCX_HEADER + b"content") == "docx"


def test_detect_unknown_type():
    """Test unknown type detection."""
    assert detect_file_type(b"unknown content") is None


def test_get_pdf_page_count_simple():
    """Test PDF page count extraction."""
    # Simple PDF with page markers
    pdf_content = b"%PDF-1.4\n1 0 obj\n/Type /Page\nendobj\n2 0 obj\n/Type /Page\nendobj\n"
    count = get_pdf_page_count(pdf_content)
    assert count == 2


def test_get_pdf_page_count_none():
    """Test PDF page count returns None for invalid content."""
    count = get_pdf_page_count(b"not a pdf")
    assert count is None


def test_validate_document_pdf():
    """Test full document validation for PDF."""
    pdf_data = PDF_HEADER + b"1 0 obj\n/Type /Page\nendobj\n" + b"x" * 1000
    result = validate_document(pdf_data, "test.pdf")
    assert result["extension"] == ".pdf"
    assert result["detected_type"] == "pdf"
    assert result["page_count"] == 1


def test_validate_document_docx():
    """Test full document validation for DOCX."""
    docx_data = DOCX_HEADER + b"content" + b"x" * 1000
    result = validate_document(docx_data, "test.docx")
    assert result["extension"] == ".docx"
    assert result["detected_type"] == "docx"


def test_validate_document_invalid_extension():
    """Test document validation with invalid extension."""
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_document(b"content", "test.txt")
    assert exc_info.value.code == "INVALID_EXTENSION"


def test_validate_document_no_extension():
    """Test document validation with no extension."""
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_document(b"content", "noextension")
    assert exc_info.value.code == "INVALID_FILENAME"


def test_validate_document_bad_signature():
    """Test document validation with mismatched signature."""
    # Need enough data to pass size check but fail signature check
    bad_pdf = b"Not a PDF at all" + b"x" * 200
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_document(bad_pdf, "test.pdf")
    assert exc_info.value.code == "INVALID_SIGNATURE"
