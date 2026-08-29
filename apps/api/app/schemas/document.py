"""Document schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response."""

    id: str
    organization_id: str
    uploaded_by: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    status: str
    document_type: str | None
    page_count: int | None
    created_at: str

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Document upload response."""

    id: str
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
