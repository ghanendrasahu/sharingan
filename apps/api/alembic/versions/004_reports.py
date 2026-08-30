"""Add reports table

Revision ID: 004_reports
Revises: 003_analysis_results
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "004_reports"
down_revision: str | None = "003_analysis_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "report_type",
            sa.String(50),
            nullable=False,
            server_default="full_analysis",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("sections", sa.Text(), nullable=True),
        sa.Column("risk_summary", sa.Text(), nullable=True),
        sa.Column("key_terms", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column(
            "overall_risk_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "risk_level", sa.String(20), nullable=False, server_default="low"
        ),
        sa.Column("processing_time_ms", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("reports")
