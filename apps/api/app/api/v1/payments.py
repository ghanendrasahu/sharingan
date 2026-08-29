"""Payment API endpoints for Razorpay integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Request

from app.models.payment import PLANS, PlanType
from app.schemas.payment import (
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    PlanResponse,
    PlansListResponse,
    SubscriptionResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    WebhookResponse,
)
from app.services.payment import payment_service

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans", response_model=PlansListResponse)
async def list_plans() -> PlansListResponse:
    """List all available subscription plans."""
    plans = []
    for _plan_type, plan in PLANS.items():
        plans.append(
            PlanResponse(
                plan_id=plan.plan_id,
                name=plan.name,
                plan_type=plan.plan_type,
                price_inr=plan.price_inr,
                credits_per_month=plan.credits_per_month,
                max_documents=plan.max_documents,
                max_upload_size_mb=plan.max_upload_size_mb,
                features=plan.features,
            )
        )
    return PlansListResponse(plans=plans)


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: CurrentUser,
) -> CreateOrderResponse:
    """Create a Razorpay order for subscription."""
    plan_type = PlanType(request.plan_type)

    order = await payment_service.create_order(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        plan_type=plan_type,
    )

    return CreateOrderResponse(
        order_id=order["order_id"],
        amount=order["amount"],
        currency=order["currency"],
        plan_id=order["plan_id"],
        plan_name=order["plan_name"],
        razorpay_key_id=payment_service.razorpay_key_id,
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: CurrentUser,
) -> VerifyPaymentResponse:
    """Verify payment and activate subscription."""
    verified = await payment_service.verify_payment(
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
    )

    if verified:
        return VerifyPaymentResponse(
            verified=True,
            message="Payment verified and subscription activated",
            subscription_id="sub_new",
        )

    return VerifyPaymentResponse(
        verified=False,
        message="Payment verification failed",
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: CurrentUser,
) -> SubscriptionResponse:
    """Get current user's subscription."""
    subscription = await payment_service.get_subscription(str(current_user.id))

    if subscription:
        return SubscriptionResponse(
            subscription_id=subscription.subscription_id,
            plan_type=subscription.plan_type,
            status=subscription.status,
            credits_remaining=subscription.credits_remaining,
            credits_used=subscription.credits_used,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
        )

    return SubscriptionResponse(
        subscription_id="sub_free",
        plan_type="free",
        status="active",
        credits_remaining=5,
        credits_used=0,
        started_at="2024-01-01T00:00:00Z",
    )


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: CurrentUser,
) -> CancelSubscriptionResponse:
    """Cancel subscription."""
    cancelled = await payment_service.cancel_subscription(request.subscription_id)

    return CancelSubscriptionResponse(
        subscription_id=request.subscription_id,
        cancelled=cancelled,
        message="Subscription cancelled" if cancelled else "Cancellation failed",
    )


@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(request: Request) -> WebhookResponse:
    """Handle Razorpay webhook events."""
    payload = await request.json()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        result = await payment_service.handle_webhook(payload, signature)
        return WebhookResponse(
            status="processed",
            event=result.get("event", "unknown"),
            message="Webhook processed successfully",
        )
    except Exception as e:
        return WebhookResponse(
            status="error",
            event=payload.get("event", "unknown"),
            message=str(e),
        )
