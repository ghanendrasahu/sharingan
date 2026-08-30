"""Payment and subscription SQLAlchemy models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    plan_type = Column(String(50), nullable=False, default="free")
    status = Column(String(50), nullable=False, default=SubscriptionStatus.ACTIVE)
    credits_remaining = Column(Integer, nullable=False, default=5)
    credits_used = Column(Integer, nullable=False, default=0)
    razorpay_subscription_id = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC), onupdate=lambda: datetime.now(tz=UTC))

    # Relationships
    payments = relationship("PaymentRecord", back_populates="subscription")

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

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    subscription_id = Column(UUID(as_uuid=False), ForeignKey("subscriptions.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    amount_inr = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    status = Column(String(50), nullable=False, default=PaymentStatus.PENDING)
    plan_type = Column(String(50), nullable=False)
    razorpay_order_id = Column(String(255), nullable=True, index=True)
    razorpay_payment_id = Column(String(255), nullable=True, index=True)
    razorpay_signature = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

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

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tz=UTC))
