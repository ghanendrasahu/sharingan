"""Add payment tables

Revision ID: 005
Revises: 004
Create Date: 2026-08-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005"
down_revision = "004_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("plan_type", sa.String(50), nullable=False, server_default="free"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("credits_remaining", sa.Integer, nullable=False, server_default="5"),
        sa.Column("credits_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("razorpay_subscription_id", sa.String(255), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # Payment records table
    op.create_table(
        "payment_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("amount_inr", sa.Float, nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("plan_type", sa.String(50), nullable=False),
        sa.Column("razorpay_order_id", sa.String(255), nullable=True, index=True),
        sa.Column("razorpay_payment_id", sa.String(255), nullable=True, index=True),
        sa.Column("razorpay_signature", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Webhook events table
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("payment_records")
    op.drop_table("subscriptions")
