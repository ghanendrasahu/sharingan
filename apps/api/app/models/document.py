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
