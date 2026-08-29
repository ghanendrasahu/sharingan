"""Document API endpoints."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, RequireRole
from app.core.config import get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.organization import MemberRole, OrganizationMember
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    PresignedUrlResponse,
)
from app.services.storage import (
    calculate_file_hash,
    ensure_bucket_exists,
    generate_presigned_url,
    generate_storage_key,
    upload_file,
)
from app.services.validation import (
    DocumentValidationError,
    validate_document,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()

# Allowed extensions (for quick check before full validation)
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile,
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Document:
    """Upload a document to the organization.

    Validates file type, signature, and size before upload.
    """
    # Quick extension check
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()

    # Validate file size early
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Full validation (signature, content type, page count)
    try:
        validation_result = validate_document(
            data=content,
            filename=file.filename,
            content_type=file.content_type,
        )
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail,
        ) from e

    # Ensure bucket exists
    ensure_bucket_exists()

    # Generate storage key
    storage_key = generate_storage_key(
        organization_id=str(organization_id),
        filename=file.filename,
        content_type=validation_result["content_type"],
    )

    # Calculate file hash
    file_hash = calculate_file_hash(content)

    # Check for duplicate
    existing = await db.execute(select(Document).where(Document.file_hash == file_hash))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document with same content already exists",
        )

    # Upload to storage
    upload_result = await upload_file(
        data=content,
        storage_key=storage_key,
        content_type=validation_result["content_type"],
        metadata={
            "organization_id": str(organization_id),
            "uploaded_by": str(current_user.id),
            "original_filename": file.filename,
        },
    )

    # Create document record
    document = Document(
        organization_id=organization_id,
        uploaded_by=current_user.id,
        filename=storage_key.split("/")[-1],
        original_filename=file.filename,
        storage_key=storage_key,
        file_size=upload_result["size"],
        content_type=validation_result["content_type"],
        file_hash=file_hash,
        status=DocumentStatus.UPLOADED,
        page_count=validation_result.get("page_count"),
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    return document


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List documents in the organization."""
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Document)
        .where(Document.organization_id == organization_id)
        .where(Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    documents = list(result.scalars().all())

    # Get total count
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count(Document.id))
        .where(Document.organization_id == organization_id)
        .where(Document.deleted_at.is_(None))
    )
    total = count_result.scalar() or 0

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Document:
    """Get document details."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get(
    "/{document_id}/download",
    response_model=PresignedUrlResponse,
)
async def get_document_download_url(
    document_id: UUID,
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(  # noqa: B008
        RequireRole(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER)  # noqa: B008
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    """Get a presigned URL for downloading the document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    url = generate_presigned_url(document.storage_key, expiration=3600)

    return {
        "url": url,
        "expires_in": 3600,
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    organization_id: UUID,
    current_user: CurrentUser,
    _membership: OrganizationMember = Depends(RequireRole(MemberRole.OWNER, MemberRole.ADMIN)),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a document (soft delete)."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    from datetime import datetime

    document.deleted_at = datetime.now(UTC)
    await db.flush()
