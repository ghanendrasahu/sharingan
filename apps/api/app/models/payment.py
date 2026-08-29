"""Payment and subscription models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class PlanType(StrEnum):
    """Subscription plan types."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class PaymentStatus(StrEnum):
    """Payment status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class SubscriptionStatus(StrEnum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIAL = "trial"
    EXPIRED = "expired"


@dataclass
class Plan:
    """Subscription plan details."""

    plan_id: str
    name: str
    plan_type: PlanType
    price_inr: float  # Price in Indian Rupees
    credits_per_month: int
    max_documents: int
    max_upload_size_mb: int
    features: list[str] = field(default_factory=list)


# Predefined plans
PLANS = {
    PlanType.FREE: Plan(
        plan_id="plan_free",
        name="Free Plan",
        plan_type=PlanType.FREE,
        price_inr=0.0,
        credits_per_month=5,
        max_documents=10,
        max_upload_size_mb=10,
        features=["Basic analysis", "5 analyses/month"],
    ),
    PlanType.STARTER: Plan(
        plan_id="plan_starter",
        name="Starter Plan",
        plan_type=PlanType.STARTER,
        price_inr=999.0,
        credits_per_month=50,
        max_documents=100,
        max_upload_size_mb=25,
        features=["Full analysis", "50 analyses/month", "Email support"],
    ),
    PlanType.PROFESSIONAL: Plan(
        plan_id="plan_professional",
        name="Professional Plan",
        plan_type=PlanType.PROFESSIONAL,
        price_inr=2999.0,
        credits_per_month=200,
        max_documents=500,
        max_upload_size_mb=50,
        features=["Full analysis", "200 analyses/month", "Priority support", "API access"],
    ),
    PlanType.ENTERPRISE: Plan(
        plan_id="plan_enterprise",
        name="Enterprise Plan",
        plan_type=PlanType.ENTERPRISE,
        price_inr=9999.0,
        credits_per_month=1000,
        max_documents=-1,  # Unlimited
        max_upload_size_mb=100,
        features=["Unlimited analysis", "Custom integrations", "Dedicated support"],
    ),
}


@dataclass
class Subscription:
    """User subscription."""

    subscription_id: str
    user_id: str
    organization_id: str
    plan_type: PlanType = PlanType.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    credits_remaining: int = 5
    credits_used: int = 0
    started_at: str = ""
    expires_at: str | None = None
    cancelled_at: str | None = None
    razorpay_subscription_id: str | None = None

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(tz=UTC).isoformat()

    @property
    def plan(self) -> Plan:
        """Get current plan details."""
        return PLANS[self.plan_type]

    @property
    def has_credits(self) -> bool:
        """Check if user has credits remaining."""
        return self.credits_remaining > 0

    def use_credit(self) -> bool:
        """Use one credit. Returns True if successful."""
        if self.credits_remaining > 0:
            self.credits_remaining -= 1
            self.credits_used += 1
            return True
        return False

    def add_credits(self, amount: int) -> None:
        """Add credits to subscription."""
        self.credits_remaining += amount

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "plan_type": self.plan_type,
            "status": self.status,
            "credits_remaining": self.credits_remaining,
            "credits_used": self.credits_used,
            "started_at": self.started_at,
            "expires_at": self.expires_at,
        }


@dataclass
class Payment:
    """Payment transaction."""

    payment_id: str
    user_id: str
    organization_id: str
    amount_inr: float
    status: PaymentStatus = PaymentStatus.PENDING
    plan_type: PlanType = PlanType.STARTER
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    created_at: str = ""
    completed_at: str | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(tz=UTC).isoformat()

    def complete(self, razorpay_payment_id: str, signature: str) -> None:
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED
        self.razorpay_payment_id = razorpay_payment_id
        self.razorpay_signature = signature
        self.completed_at = datetime.now(tz=UTC).isoformat()

    def fail(self) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "amount_inr": self.amount_inr,
            "status": self.status,
            "plan_type": self.plan_type,
            "created_at": self.created_at,
        }
