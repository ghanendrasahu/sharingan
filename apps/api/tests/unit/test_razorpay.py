"""Unit tests for Razorpay payment integration."""

import pytest

from app.models.payment import (
    PLANS,
    Payment,
    PaymentStatus,
    PlanType,
    Subscription,
    SubscriptionStatus,
)
from app.services.payment import PaymentService


@pytest.fixture
def payment_service() -> PaymentService:
    """Create a payment service instance."""
    return PaymentService()


def test_plan_type_enum():
    """Test plan type enum values."""
    assert PlanType.FREE == "free"
    assert PlanType.STARTER == "starter"
    assert PlanType.PROFESSIONAL == "professional"
    assert PlanType.ENTERPRISE == "enterprise"


def test_payment_status_enum():
    """Test payment status enum values."""
    assert PaymentStatus.PENDING == "pending"
    assert PaymentStatus.COMPLETED == "completed"
    assert PaymentStatus.FAILED == "failed"


def test_plans_available():
    """Test that all plans are available."""
    assert len(PLANS) == 4
    assert PlanType.FREE in PLANS
    assert PlanType.STARTER in PLANS


def test_plan_details():
    """Test plan details."""
    plan = PLANS[PlanType.PROFESSIONAL]
    assert plan.price_inr == 2999.0
    assert plan.credits_per_month == 200


@pytest.mark.asyncio
async def test_create_order(payment_service: PaymentService):
    """Test order creation."""
    order = await payment_service.create_order(
        user_id="user_123",
        organization_id="org_123",
        plan_type=PlanType.STARTER,
    )

    assert order["order_id"].startswith("order_")
    assert order["amount"] == 99900  # 999 * 100 paise
    assert order["currency"] == "INR"
    assert order["plan_name"] == "Starter Plan"


@pytest.mark.asyncio
async def test_create_order_free_plan(payment_service: PaymentService):
    """Test order creation for free plan."""
    order = await payment_service.create_order(
        user_id="user_123",
        organization_id="org_123",
        plan_type=PlanType.FREE,
    )

    assert order["amount"] == 0


@pytest.mark.asyncio
async def test_create_subscription(payment_service: PaymentService):
    """Test subscription creation."""
    subscription = await payment_service.create_subscription(
        user_id="user_123",
        organization_id="org_123",
        plan_type=PlanType.STARTER,
    )

    assert subscription.plan_type == PlanType.STARTER
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.credits_remaining == 50


@pytest.mark.asyncio
async def test_get_subscription(payment_service: PaymentService):
    """Test getting user subscription."""
    subscription = await payment_service.get_subscription("user_123")

    assert subscription is not None
    assert subscription.plan_type == PlanType.FREE


@pytest.mark.asyncio
async def test_cancel_subscription(payment_service: PaymentService):
    """Test subscription cancellation."""
    subscription = await payment_service.create_subscription(
        user_id="user_123",
        organization_id="org_123",
        plan_type=PlanType.STARTER,
    )

    result = await payment_service.cancel_subscription(subscription.subscription_id)
    assert result is True


@pytest.mark.asyncio
async def test_get_payment_history(payment_service: PaymentService):
    """Test getting payment history."""
    history = await payment_service.get_payment_history("user_123")
    assert isinstance(history, list)


@pytest.mark.asyncio
async def test_handle_webhook(payment_service: PaymentService):
    """Test webhook handling."""
    payload = {"event": "payment.captured", "payload": {}}
    result = await payment_service.handle_webhook(payload, "test_signature")

    assert result["status"] == "processed"
    assert result["event"] == "payment.captured"


@pytest.mark.asyncio
async def test_handle_webhook_unhandled(payment_service: PaymentService):
    """Test handling unhandled webhook event."""
    payload = {"event": "unknown.event", "payload": {}}
    result = await payment_service.handle_webhook(payload, "test_signature")

    assert result["status"] == "unhandled_event"


def test_payment_creation():
    """Test payment model creation."""
    payment = Payment(
        payment_id="pay_123",
        user_id="user_123",
        organization_id="org_123",
        amount_inr=999.0,
        plan_type=PlanType.STARTER,
    )
    assert payment.status == PaymentStatus.PENDING


def test_payment_complete():
    """Test completing a payment."""
    payment = Payment(
        payment_id="pay_123",
        user_id="user_123",
        organization_id="org_123",
        amount_inr=999.0,
        plan_type=PlanType.STARTER,
    )
    payment.complete("razorpay_pay_123", "signature_123")
    assert payment.status == PaymentStatus.COMPLETED
    assert payment.razorpay_payment_id == "razorpay_pay_123"


def test_subscription_use_credit():
    """Test using a credit."""
    sub = Subscription(
        subscription_id="sub_123",
        user_id="user_123",
        organization_id="org_123",
        credits_remaining=1,
    )
    result = sub.use_credit()
    assert result is True
    assert sub.credits_remaining == 0
    assert sub.credits_used == 1


def test_subscription_no_credits():
    """Test subscription with no credits."""
    sub = Subscription(
        subscription_id="sub_123",
        user_id="user_123",
        organization_id="org_123",
        credits_remaining=0,
    )
    result = sub.use_credit()
    assert result is False
    assert sub.credits_remaining == 0


def test_subscription_add_credits():
    """Test adding credits to subscription."""
    sub = Subscription(
        subscription_id="sub_123",
        user_id="user_123",
        organization_id="org_123",
        credits_remaining=5,
    )
    sub.add_credits(10)
    assert sub.credits_remaining == 15
