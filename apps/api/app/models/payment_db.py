"""Payment and subscription SQLAlchemy models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


class SubscriptionStatus:
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIAL = "trial"
    EXPIRED = "expired"


class PaymentStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """User subscription persisted to database."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SubscriptionStatus.ACTIVE)
    credits_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC), onupdate=lambda: datetime.now(tz=UTC))

    # Relationships
    payments: Mapped[list[PaymentRecord]] = relationship("PaymentRecord", back_populates="subscription")

    @property
    def has_credits(self) -> bool:
        return self.credits_remaining > 0

    def use_credit(self) -> bool:
        if self.credits_remaining > 0:
            self.credits_remaining -= 1
            self.credits_used += 1
            return True
        return False

    def add_credits(self, amount: int) -> None:
        self.credits_remaining += amount


class PaymentRecord(Base):
    """Payment transaction persisted to database."""

    __tablename__ = "payment_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    subscription_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("subscriptions.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=PaymentStatus.PENDING)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    razorpay_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    subscription: Mapped[Subscription] = relationship("Subscription", back_populates="payments")

    def complete(self, razorpay_payment_id: str, signature: str) -> None:
        self.status = PaymentStatus.COMPLETED
        self.razorpay_payment_id = razorpay_payment_id
        self.razorpay_signature = signature
        self.completed_at = datetime.now(tz=UTC)

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED


class WebhookEvent(Base):
    """Razorpay webhook events for idempotency."""

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
