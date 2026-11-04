"""Add missing document_clauses columns used by the ORM.

Revision ID: 006_document_clause_content
Revises: 005
Create Date: 2026-11-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006_document_clause_content"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_clauses",
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "document_clauses",
        sa.Column("clause_index", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("document_clauses", "clause_index")
    op.drop_column("document_clauses", "content")
