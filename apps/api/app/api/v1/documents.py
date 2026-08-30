"""Document API endpoints."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
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
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
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
        filename=file.filename or "document",
        content_type=str(validation_result.get("content_type", "application/octet-stream")),
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
        content_type=str(validation_result.get("content_type", "application/octet-stream")),
        metadata={
            "organization_id": str(organization_id),
            "uploaded_by": str(current_user.id),
            "original_filename": file.filename or "document",
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


class CompareRequest(BaseModel):
    """Request to compare two document versions."""

    document_id_a: str = Field(..., description="First document ID")
    document_id_b: str = Field(..., description="Second document ID")


class ClauseDiff(BaseModel):
    """Difference in a clause between versions."""

    clause_type: str
    status: str  # added, removed, modified, unchanged
    content_a: str | None = None
    content_b: str | None = None
    summary: str = ""


class ComparisonResponse(BaseModel):
    """Response for document comparison."""

    document_id_a: str
    document_id_b: str
    summary: str
    clause_diffs: list[ClauseDiff] = Field(default_factory=list)
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
    unchanged_count: int = 0


@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    request: CompareRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ComparisonResponse:
    """Compare two document versions.

    Detects added, removed, modified, and unchanged clauses between two documents.
    """
    from app.models.document import DocumentClause, DocumentStatus

    doc_id_a = UUID(request.document_id_a)
    doc_id_b = UUID(request.document_id_b)

    # Get both documents
    result_a = await db.execute(
        select(Document).where(
            Document.id == doc_id_a,
            Document.deleted_at.is_(None),
        )
    )
    doc_a = result_a.scalar_one_or_none()

    result_b = await db.execute(
        select(Document).where(
            Document.id == doc_id_b,
            Document.deleted_at.is_(None),
        )
    )
    doc_b = result_b.scalar_one_or_none()

    if doc_a is None or doc_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both documents not found",
        )

    if doc_a.status != DocumentStatus.PROCESSED or doc_b.status != DocumentStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both documents must be processed before comparison",
        )

    # Get clauses for both documents
    clauses_a_result = await db.execute(
        select(DocumentClause)
        .where(DocumentClause.document_id == doc_id_a)
        .order_by(DocumentClause.clause_type, DocumentClause.clause_index)
    )
    clauses_a = {c.clause_type: c for c in clauses_a_result.scalars().all()}

    clauses_b_result = await db.execute(
        select(DocumentClause)
        .where(DocumentClause.document_id == doc_id_b)
        .order_by(DocumentClause.clause_type, DocumentClause.clause_index)
    )
    clauses_b = {c.clause_type: c for c in clauses_b_result.scalars().all()}

    # Compare clauses
    all_types = set(clauses_a.keys()) | set(clauses_b.keys())
    diffs: list[ClauseDiff] = []
    added = removed = modified = unchanged = 0

    for clause_type in sorted(all_types):
        clause_a = clauses_a.get(clause_type)
        clause_b = clauses_b.get(clause_type)

        if clause_a and clause_b:
            if clause_a.content.strip() == clause_b.content.strip():
                unchanged += 1
            else:
                modified += 1
                diffs.append(
                    ClauseDiff(
                        clause_type=clause_type,
                        status="modified",
                        content_a=clause_a.content[:500],
                        content_b=clause_b.content[:500],
                        summary=f"Clause '{clause_type}' was modified between versions",
                    )
                )
        elif clause_a and not clause_b:
            removed += 1
            diffs.append(
                ClauseDiff(
                    clause_type=clause_type,
                    status="removed",
                    content_a=clause_a.content[:500],
                    summary=f"Clause '{clause_type}' was removed in second version",
                )
            )
        else:
            added += 1
            diffs.append(
                ClauseDiff(
                    clause_type=clause_type,
                    status="added",
                    content_b=clause_b.content[:500] if clause_b else "",
                    summary=f"Clause '{clause_type}' was added in second version",
                )
            )

    # Generate summary
    if modified == 0 and added == 0 and removed == 0:
        summary = "Documents are identical in structure and content."
    else:
        parts = []
        if modified:
            parts.append(f"{modified} clause(s) modified")
        if added:
            parts.append(f"{added} clause(s) added")
        if removed:
            parts.append(f"{removed} clause(s) removed")
        summary = f"Comparison complete: {', '.join(parts)}."

    return ComparisonResponse(
        document_id_a=str(doc_id_a),
        document_id_b=str(doc_id_b),
        summary=summary,
        clause_diffs=diffs,
        added_count=added,
        removed_count=removed,
        modified_count=modified,
        unchanged_count=unchanged,
    )
