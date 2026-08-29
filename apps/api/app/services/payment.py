"""Payment service for Razorpay integration."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.models.payment import (
    PLANS,
    Payment,
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
        self._orders: dict[str, dict[str, Any]] = {}
        self._payments: dict[str, Payment] = {}
        self._subscriptions: dict[str, Subscription] = {}

    async def create_order(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
    ) -> dict[str, Any]:
        """Create a Razorpay order for subscription."""
        plan = PLANS[plan_type]

        order_id = f"order_{hashlib.md5(f'{user_id}{plan_type}{datetime.now(tz=UTC).isoformat()}'.encode()).hexdigest()[:12]}"

        order = {
            "order_id": order_id,
            "amount": int(plan.price_inr * 100),
            "currency": "INR",
            "plan_id": plan.plan_id,
            "plan_name": plan.name,
            "user_id": user_id,
            "organization_id": organization_id,
            "plan_type": plan_type,
            "status": "created",
            "created_at": datetime.now(tz=UTC).isoformat(),
        }

        self._orders[order_id] = order

        return {
            "order_id": order_id,
            "amount": order["amount"],
            "currency": order["currency"],
            "plan_id": plan.plan_id,
            "plan_name": plan.name,
            "razorpay_key_id": self.razorpay_key_id,
        }

    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Payment:
        """Verify Razorpay payment and create payment record."""
        # Verify signature
        if not self._verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        ):
            raise PaymentError("Invalid payment signature", code="INVALID_SIGNATURE")

        # Get order details
        order = self._orders.get(razorpay_order_id)
        if not order:
            raise PaymentError("Order not found", code="ORDER_NOT_FOUND")

        # Create payment record
        payment = Payment(
            payment_id=f"pay_{hashlib.md5(razorpay_payment_id.encode()).hexdigest()[:12]}",
            user_id=order["user_id"],
            organization_id=order["organization_id"],
            amount_inr=order["amount"] / 100,
            plan_type=order["plan_type"],
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )
        payment.complete(razorpay_payment_id, razorpay_signature)

        self._payments[payment.payment_id] = payment

        # Create subscription
        await self.create_subscription(
            user_id=order["user_id"],
            organization_id=order["organization_id"],
            plan_type=order["plan_type"],
        )

        return payment

    def _verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify Razorpay payment signature."""
        if not self.razorpay_key_secret:
            return True

        payload = f"{order_id}|{payment_id}"
        expected = hmac.new(
            self.razorpay_key_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def create_subscription(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
        razorpay_subscription_id: str | None = None,
    ) -> Subscription:
        """Create or update user subscription."""
        plan = PLANS[plan_type]

        subscription = Subscription(
            subscription_id=f"sub_{hashlib.md5(f'{user_id}{organization_id}'.encode()).hexdigest()[:12]}",
            user_id=user_id,
            organization_id=organization_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            credits_remaining=plan.credits_per_month,
            razorpay_subscription_id=razorpay_subscription_id,
        )

        self._subscriptions[subscription.subscription_id] = subscription

        return subscription

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            return True
        return False

    async def get_subscription(self, user_id: str) -> Subscription | None:
        """Get user's current subscription."""
        for sub in self._subscriptions.values():
            if sub.user_id == user_id and sub.status == SubscriptionStatus.ACTIVE:
                return sub

        return Subscription(
            subscription_id="sub_free",
            user_id=user_id,
            organization_id="org_default",
            plan_type=PlanType.FREE,
            status=SubscriptionStatus.ACTIVE,
            credits_remaining=5,
        )

    async def get_payment_history(self, user_id: str, limit: int = 10) -> list[Payment]:
        """Get payment history for a user."""
        payments = [p for p in self._payments.values() if p.user_id == user_id]
        payments.sort(key=lambda x: x.created_at or "", reverse=True)
        return payments[:limit]

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        signature: str,
    ) -> dict[str, Any]:
        """Handle Razorpay webhook event."""
        if not self._verify_webhook_signature(payload, signature):
            raise PaymentError("Invalid webhook signature", code="INVALID_SIGNATURE")

        event_type = payload.get("event", "")

        handlers: dict[str, Any] = {
            "payment.captured": self._handle_payment_captured,
            "payment.failed": self._handle_payment_failed,
            "subscription.activated": self._handle_subscription_activated,
            "subscription.cancelled": self._handle_subscription_cancelled,
            "subscription.charged": self._handle_subscription_charged,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"status": "unhandled_event", "event": event_type}

    def _verify_webhook_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        if not self.webhook_secret:
            return True

        payload_str = str(payload)
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

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
