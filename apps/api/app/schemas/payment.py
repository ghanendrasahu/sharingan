"""Payment API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    """Plan details response."""

    plan_id: str
    name: str
    plan_type: str
    price_inr: float
    credits_per_month: int
    max_documents: int
    max_upload_size_mb: int
    features: list[str] = Field(default_factory=list)


class PlansListResponse(BaseModel):
    """List of available plans."""

    plans: list[PlanResponse] = Field(default_factory=list)


class CreateOrderRequest(BaseModel):
    """Request to create payment order."""

    plan_type: str = Field(..., description="Plan type: starter, professional, enterprise")


class CreateOrderResponse(BaseModel):
    """Response with order details."""

    order_id: str
    amount: int  # Amount in paise
    currency: str = "INR"
    plan_id: str
    plan_name: str
    razorpay_key_id: str = ""


class VerifyPaymentRequest(BaseModel):
    """Request to verify payment."""

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    """Response after payment verification."""

    verified: bool
    message: str = ""
    subscription_id: str | None = None


class SubscriptionResponse(BaseModel):
    """User subscription response."""

    subscription_id: str
    plan_type: str
    status: str
    credits_remaining: int
    credits_used: int
    started_at: str
    expires_at: str | None = None


class WebhookRequest(BaseModel):
    """Razorpay webhook request."""

    event: str
    payload: dict
    created_at: int | None = None


class WebhookResponse(BaseModel):
    """Webhook processing response."""

    status: str
    event: str
    message: str = ""


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription."""

    subscription_id: str
    reason: str = ""


class CancelSubscriptionResponse(BaseModel):
    """Response after cancellation."""

    subscription_id: str
    cancelled: bool
    message: str = ""


class UsageResponse(BaseModel):
    """User usage statistics."""

    credits_remaining: int
    credits_used: int
    credits_total: int
    documents_uploaded: int
    analyses_completed: int
