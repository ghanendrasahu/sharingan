"""Document validation services - file signatures, MIME types, page counts."""

from __future__ import annotations

from pathlib import Path

# File signature (magic bytes) for validation
FILE_SIGNATURES = {
    "pdf": {
        "bytes": b"%PDF",
        "offset": 0,
        "extension": ".pdf",
        "mime": "application/pdf",
    },
    "docx": {
        # DOCX is a ZIP file containing [Content_Types].xml
        "bytes": b"PK\x03\x04",
        "offset": 0,
        "extension": ".docx",
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
}

# Maximum allowed file size per type (in bytes)
MAX_FILE_SIZES = {
    ".pdf": 50 * 1024 * 1024,  # 50MB
    ".docx": 50 * 1024 * 1024,  # 50MB
}

# Minimum file size (to detect empty/corrupt files)
MIN_FILE_SIZE = 100  # bytes


class DocumentValidationError(Exception):
    """Raised when document validation fails."""

    def __init__(self, detail: str, code: str = "VALIDATION_ERROR"):
        self.detail = detail
        self.code = code
        super().__init__(detail)


def validate_file_signature(data: bytes, expected_extension: str) -> bool:
    """Validate file content matches expected type using magic bytes."""
    if len(data) < 4:
        return False

    ext = expected_extension.lower().lstrip(".")

    if ext == "pdf":
        return data[:4] == b"%PDF"
    elif ext == "docx":
        # DOCX files are ZIP archives
        return data[:4] == b"PK\x03\x04"
    else:
        # Unknown type, cannot validate signature
        return False


def detect_file_type(data: bytes) -> str | None:
    """Detect file type from content."""
    if len(data) < 4:
        return None

    if data[:4] == b"%PDF":
        return "pdf"
    elif data[:4] == b"PK\x03\x04":
        # Could be DOCX or any ZIP file
        # For now, assume DOCX if we're in this context
        return "docx"
    return None


def validate_file_size(data: bytes, extension: str) -> None:
    """Validate file size is within limits."""
    size = len(data)
    ext = extension.lower()

    if size < MIN_FILE_SIZE:
        raise DocumentValidationError(
            f"File is too small ({size} bytes). File may be empty or corrupt.",
            code="FILE_TOO_SMALL",
        )

    max_size = MAX_FILE_SIZES.get(ext, 10 * 1024 * 1024)
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise DocumentValidationError(
            f"File is too large ({size / (1024 * 1024):.1f}MB). Maximum size: {max_mb}MB",
            code="FILE_TOO_LARGE",
        )


def get_pdf_page_count(data: bytes) -> int | None:
    """Extract page count from PDF content.

    Uses a simple heuristic - counts /Type /Page entries.
    This is a lightweight approach that doesn't require full PDF parsing.
    """
    try:
        # Simple heuristic: count occurrences of /Type /Page
        # This works for most PDFs but may not be 100% accurate
        content = data.decode("latin-1", errors="ignore")

        # Count page objects (but not /Type /Pages which is the parent)
        import re

        pages = re.findall(r"/Type\s*/Page[^s]", content)
        return len(pages) if pages else None
    except Exception:
        return None


def validate_document(
    data: bytes,
    filename: str,
    content_type: str | None = None,
) -> dict[str, str | int | None]:
    """Comprehensive document validation.

    Returns validation result with detected metadata.
    Raises DocumentValidationError if validation fails.
    """
    # Get extension
    ext = Path(filename).suffix.lower()
    if not ext:
        raise DocumentValidationError(
            "Filename must have an extension",
            code="INVALID_FILENAME",
        )

    # Validate extension
    allowed_extensions = {".pdf", ".docx"}
    if ext not in allowed_extensions:
        raise DocumentValidationError(
            f"File type not allowed: {ext}. Allowed: {', '.join(allowed_extensions)}",
            code="INVALID_EXTENSION",
        )

    # Validate file size
    validate_file_size(data, ext)

    # Validate file signature (magic bytes)
    if not validate_file_signature(data, ext):
        raise DocumentValidationError(
            f"File content does not match {ext} format. The file may be corrupt or renamed.",
            code="INVALID_SIGNATURE",
        )

    # Detect actual file type from content
    detected_type = detect_file_type(data)
    if detected_type is None:
        raise DocumentValidationError(
            "Unable to detect file type from content",
            code="DETECTION_FAILED",
        )

    # Get page count for PDFs
    page_count = None
    if ext == ".pdf":
        page_count = get_pdf_page_count(data)

    return {
        "extension": ext,
        "detected_type": detected_type,
        "content_type": f"application/{detected_type}",
        "page_count": page_count,
        "file_size": len(data),
    }
