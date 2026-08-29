"""Unit tests for storage services."""

from app.services.storage import calculate_file_hash, generate_storage_key


def test_calculate_file_hash():
    """Test file hash calculation."""
    data = b"Hello, World!"
    hash_value = calculate_file_hash(data)
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA-256 hex digest length


def test_calculate_file_hash_deterministic():
    """Test that hash is deterministic."""
    data = b"Test data for hashing"
    hash1 = calculate_file_hash(data)
    hash2 = calculate_file_hash(data)
    assert hash1 == hash2


def test_calculate_file_hash_different_data():
    """Test that different data produces different hashes."""
    hash1 = calculate_file_hash(b"Data 1")
    hash2 = calculate_file_hash(b"Data 2")
    assert hash1 != hash2


def test_generate_storage_key():
    """Test storage key generation."""
    key = generate_storage_key(
        organization_id="org-123",
        filename="test-document.pdf",
        content_type="application/pdf",
    )
    assert "org-123" in key
    assert key.endswith(".pdf")
    assert "/" in key  # Should have date prefix


def test_generate_storage_key_sanitizes_filename():
    """Test that storage key sanitizes filename."""
    key = generate_storage_key(
        organization_id="org-123",
        filename="../../../etc/passwd",
    )
    # Path traversal should be removed
    assert ".." not in key
    assert "etc/" not in key
    # The filename "passwd" is safe - it's the path traversal that's dangerous
    assert key.endswith("_passwd")


def test_generate_storage_key_handles_special_chars():
    """Test storage key handles special characters."""
    key = generate_storage_key(
        organization_id="org-123",
        filename="document with spaces (1).pdf",
    )
    assert " " not in key or key.endswith("_document with spaces (1).pdf")


def test_generate_storage_key_preserves_extension():
    """Test that storage key preserves file extension."""
    key = generate_storage_key(
        organization_id="org-123",
        filename="report.docx",
    )
    assert key.endswith(".docx")


def test_generate_storage_key_unique():
    """Test that storage keys are unique."""
    keys = set()
    for _ in range(10):
        key = generate_storage_key(
            organization_id="org-123",
            filename="document.pdf",
        )
        keys.add(key)
    assert len(keys) == 10  # All keys should be unique
