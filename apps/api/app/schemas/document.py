"""Document schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves this annotation at runtime
from uuid import UUID  # noqa: TC003 - Pydantic resolves this annotation at runtime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response."""

    id: UUID
    organization_id: UUID
    uploaded_by: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    status: str
    document_type: str | None
    page_count: int | None
    processing_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Document upload response."""

    id: UUID
    filename: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class PresignedUrlResponse(BaseModel):
    """Presigned URL response."""

    url: str
    expires_in: int
