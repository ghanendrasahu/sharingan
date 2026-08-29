"""Unit tests for payment and subscription models."""

from app.models.payment import (
    PLANS,
    Payment,
    PaymentStatus,
    PlanType,
    Subscription,
    SubscriptionStatus,
)
from app.schemas.payment import (
    PlanResponse,
    SubscriptionResponse,
    WebhookRequest,
)


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


def test_subscription_status_enum():
    """Test subscription status enum values."""
    assert SubscriptionStatus.ACTIVE == "active"
    assert SubscriptionStatus.CANCELLED == "cancelled"


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


def test_subscription_creation():
    """Test subscription model creation."""
    sub = Subscription(
        subscription_id="sub_123",
        user_id="user_123",
        organization_id="org_123",
        plan_type=PlanType.STARTER,
        credits_remaining=50,
    )
    assert sub.plan_type == PlanType.STARTER
    assert sub.has_credits is True


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


def test_plan_response_schema():
    """Test plan response schema."""
    response = PlanResponse(
        plan_id="plan_123",
        name="Test Plan",
        plan_type="starter",
        price_inr=999.0,
        credits_per_month=50,
        max_documents=100,
        max_upload_size_mb=25,
    )
    assert response.plan_type == "starter"


def test_subscription_response_schema():
    """Test subscription response schema."""
    response = SubscriptionResponse(
        subscription_id="sub_123",
        plan_type="starter",
        status="active",
        credits_remaining=50,
        credits_used=0,
        started_at="2024-01-01T00:00:00Z",
    )
    assert response.credits_remaining == 50


def test_webhook_request_schema():
    """Test webhook request schema."""
    request = WebhookRequest(
        event="payment.captured",
        payload={"payment": {"entity": {}}},
    )
    assert request.event == "payment.captured"
