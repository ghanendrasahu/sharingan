"""Report models."""

from __future__ import annotations

import enum
from uuid import UUID  # noqa: TC003

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportStatus(enum.StrEnum):
    """Report generation status."""

    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Report(UUIDMixin, TimestampMixin, Base):
    """Generated analysis report."""

    __tablename__ = "reports"

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="full_analysis",
    )
    status: Mapped[ReportStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ReportStatus.PENDING,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    executive_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sections: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    risk_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    key_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    recommendations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    overall_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="low",
    )
    processing_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} doc={self.document_id}>"
