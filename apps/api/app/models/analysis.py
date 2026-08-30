"""Analysis result models."""

from __future__ import annotations

import enum
from uuid import UUID  # noqa: TC003

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AnalysisStatus(enum.StrEnum):
    """Analysis processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisResult(UUIDMixin, TimestampMixin, Base):
    """AI analysis result for a document."""

    __tablename__ = "analysis_results"

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
    analysis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="full_analysis",
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AnalysisStatus.PENDING,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    overall_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    high_risk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    medium_risk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    low_risk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    recommendations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    model_used: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
        return f"<AnalysisResult doc={self.document_id} score={self.overall_risk_score}>"


class AnalysisRisk(UUIDMixin, TimestampMixin, Base):
    """Individual risk finding from AI analysis."""

    __tablename__ = "analysis_risks"

    analysis_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="low",
    )
    clause_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    def __repr__(self) -> str:
        return f"<AnalysisRisk {self.risk_id} severity={self.severity}>"
