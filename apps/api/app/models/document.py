"""Document models."""

from __future__ import annotations

import enum
from uuid import UUID  # noqa: TC003

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class DocumentStatus(enum.StrEnum):
    """Document processing status."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class DocumentType(enum.StrEnum):
    """Document classification types."""

    EMPLOYMENT = "employment"
    NDA = "nda"
    LEASE = "lease"
    VENDOR = "vendor"
    CONSULTANCY = "consultancy"
    FOUNDER = "founder"
    TERM_SHEET = "term_sheet"
    OTHER = "other"
    UNKNOWN = "unknown"


class Document(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Document metadata model."""

    __tablename__ = "documents"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )
    document_type: Mapped[DocumentType | None] = mapped_column(
        String(20),
        nullable=True,
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Document {self.original_filename}>"


class DocumentVersion(UUIDMixin, TimestampMixin, Base):
    """Document version model for tracking changes."""

    __tablename__ = "document_versions"

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DocumentVersion doc={self.document_id} v{self.version_number}>"


class DocumentPage(UUIDMixin, TimestampMixin, Base):
    """Extracted page content from a document."""

    __tablename__ = "document_pages"

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    word_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    has_images: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    is_scanned: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return f"<DocumentPage doc={self.document_id} p{self.page_number}>"


class DocumentClause(UUIDMixin, TimestampMixin, Base):
    """Segmented clause from a document."""

    __tablename__ = "document_clauses"

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clause_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    clause_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="other",
    )
    clause_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    char_start: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    char_end: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DocumentClause {self.clause_id} type={self.clause_type}>"
