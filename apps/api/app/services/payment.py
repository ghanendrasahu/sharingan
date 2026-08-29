"""Payment service for Razorpay integration."""

from __future__ import annotations

import hashlib
from typing import Any

from app.core.config import get_settings
from app.models.payment import (
    PlanType,
    Subscription,
    SubscriptionStatus,
)

settings = get_settings()


class PaymentError(Exception):
    """Payment processing error."""

    def __init__(self, message: str, code: str = "PAYMENT_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class PaymentService:
    """Service for payment operations."""

    def __init__(self) -> None:
        self.razorpay_key_id = settings.RAZORPAY_KEY_ID
        self.razorpay_key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    async def create_order(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
    ) -> dict[str, Any]:
        """Create a Razorpay order for subscription."""
        from app.models.payment import PLANS

        plan = PLANS[plan_type]

        # In production, this would call Razorpay API
        # For now, return mock order
        order_id = f"order_{hashlib.md5(f'{user_id}{plan_type}'.encode()).hexdigest()[:12]}"

        return {
            "order_id": order_id,
            "amount": int(plan.price_inr * 100),  # Amount in paise
            "currency": "INR",
            "plan_id": plan.plan_id,
            "plan_name": plan.name,
        }

    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify Razorpay payment signature."""
        # In production, verify with Razorpay
        # For now, return mock verification
        return True

    async def create_subscription(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
        razorpay_subscription_id: str | None = None,
    ) -> Subscription:
        """Create or update user subscription."""
        from app.models.payment import PLANS

        plan = PLANS[plan_type]

        subscription = Subscription(
            subscription_id=f"sub_{hashlib.md5(f'{user_id}'.encode()).hexdigest()[:12]}",
            user_id=user_id,
            organization_id=organization_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            credits_remaining=plan.credits_per_month,
            razorpay_subscription_id=razorpay_subscription_id,
        )

        # In production, save to database
        return subscription

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription."""
        # In production, cancel with Razorpay
        return True

    async def get_subscription(self, user_id: str) -> Subscription | None:
        """Get user's current subscription."""
        # In production, fetch from database
        return Subscription(
            subscription_id="sub_mock",
            user_id=user_id,
            organization_id="org_mock",
            plan_type=PlanType.FREE,
            credits_remaining=5,
        )

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        signature: str,
    ) -> dict[str, Any]:
        """Handle Razorpay webhook event."""
        # Verify signature
        if not self._verify_webhook_signature(payload, signature):
            raise PaymentError("Invalid webhook signature", code="INVALID_SIGNATURE")

        event_type = payload.get("event", "")

        if event_type == "payment.captured":
            return await self._handle_payment_captured(payload)
        elif event_type == "payment.failed":
            return await self._handle_payment_failed(payload)
        elif event_type == "subscription.activated":
            return await self._handle_subscription_activated(payload)
        elif event_type == "subscription.cancelled":
            return await self._handle_subscription_cancelled(payload)
        elif event_type == "subscription.charged":
            return await self._handle_subscription_charged(payload)

        return {"status": "unhandled_event", "event": event_type}

    def _verify_webhook_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        # In production, verify HMAC signature
        return True

    async def _handle_payment_captured(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle payment captured event."""
        return {"status": "processed", "event": "payment.captured"}

    async def _handle_payment_failed(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle payment failed event."""
        return {"status": "processed", "event": "payment.failed"}

    async def _handle_subscription_activated(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription activated event."""
        return {"status": "processed", "event": "subscription.activated"}

    async def _handle_subscription_cancelled(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription cancelled event."""
        return {"status": "processed", "event": "subscription.cancelled"}

    async def _handle_subscription_charged(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription charged event (renewal)."""
        return {"status": "processed", "event": "subscription.charged"}


payment_service = PaymentService()
