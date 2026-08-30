"""Payment service with database persistence."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from app.core.config import get_settings
from app.models.payment import PLANS, PlanType
from app.models.payment_db import (
    PaymentRecord,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
    WebhookEvent,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class PaymentError(Exception):
    """Payment processing error."""

    def __init__(self, message: str, code: str = "PAYMENT_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class PaymentService:
    """Service for payment operations with database persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.razorpay_key_id = settings.RAZORPAY_KEY_ID
        self.razorpay_key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self._client = None

    def _get_razorpay_client(self):
        """Get or create Razorpay client."""
        if self._client is None and self.razorpay_key_id and self.razorpay_key_secret:
            try:
                import razorpay

                self._client = razorpay.Client(
                    auth=(self.razorpay_key_id, self.razorpay_key_secret)
                )
            except ImportError:
                logger.warning("razorpay package not installed")
        return self._client

    async def create_order(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
    ) -> dict[str, Any]:
        """Create a Razorpay order for subscription."""
        plan = PLANS[plan_type]
        amount_paise = int(plan.price_inr * 100)

        # Get or create subscription
        subscription = await self._get_or_create_subscription(user_id, organization_id, plan_type)

        # Try real Razorpay API first
        client = self._get_razorpay_client()
        if client and plan.price_inr > 0:
            try:
                order = client.order.create(  # type: ignore[union-attr]
                    {
                        "amount": amount_paise,
                        "currency": "INR",
                        "receipt": f"sub_{subscription.id}",
                        "notes": {
                            "user_id": user_id,
                            "organization_id": organization_id,
                            "plan_type": plan_type.value,
                        },
                    }
                )
                razorpay_order_id = order.get("id", "")
            except Exception:
                logger.exception("Razorpay order creation failed, using mock")
                razorpay_order_id = f"order_{hashlib.md5(f'{user_id}{plan_type}{datetime.now(tz=UTC).isoformat()}'.encode(), usedforsecurity=False).hexdigest()[:12]}"
        else:
            # Mock order for free plans or when Razorpay not configured
            razorpay_order_id = f"order_{hashlib.md5(f'{user_id}{plan_type}{datetime.now(tz=UTC).isoformat()}'.encode(), usedforsecurity=False).hexdigest()[:12]}"

        # Create payment record
        payment = PaymentRecord(
            subscription_id=subscription.id,
            user_id=user_id,
            organization_id=organization_id,
            amount_inr=plan.price_inr,
            plan_type=plan_type.value,
            razorpay_order_id=razorpay_order_id,
        )
        self.db.add(payment)
        await self.db.flush()

        return {
            "order_id": razorpay_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "plan_id": plan.plan_id,
            "plan_name": plan.name,
            "razorpay_key_id": self.razorpay_key_id,
        }

    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> PaymentRecord:
        """Verify Razorpay payment and update payment record."""
        if not self._verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        ):
            raise PaymentError("Invalid payment signature", code="INVALID_SIGNATURE")

        # Find payment record
        result = await self.db.execute(
            select(PaymentRecord).where(PaymentRecord.razorpay_order_id == razorpay_order_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise PaymentError("Order not found", code="ORDER_NOT_FOUND")

        # Update payment
        payment.complete(razorpay_payment_id, razorpay_signature)
        await self.db.flush()

        # Update subscription
        subscription_result = await self.db.execute(
            select(Subscription).where(Subscription.id == payment.subscription_id)
        )
        subscription = subscription_result.scalar_one_or_none()
        if subscription:
            plan = PLANS[PlanType(payment.plan_type)]
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.credits_remaining = plan.credits_per_month
            await self.db.flush()

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

    async def _get_or_create_subscription(
        self,
        user_id: str,
        organization_id: str,
        plan_type: PlanType,
    ) -> Subscription:
        """Get or create subscription for user."""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.organization_id == organization_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            plan = PLANS[plan_type]
            subscription = Subscription(
                user_id=user_id,
                organization_id=organization_id,
                plan_type=plan_type.value,
                status=SubscriptionStatus.ACTIVE,
                credits_remaining=plan.credits_per_month,
            )
            self.db.add(subscription)
            await self.db.flush()

        return subscription

    async def get_subscription(self, user_id: str) -> Subscription | None:
        """Get user's current subscription."""
        result = await self.db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.now(tz=UTC)
            await self.db.flush()
            return True
        return False

    async def get_payment_history(self, user_id: str, limit: int = 10) -> list[PaymentRecord]:
        """Get payment history for a user."""
        result = await self.db.execute(
            select(PaymentRecord)
            .where(PaymentRecord.user_id == user_id)
            .order_by(PaymentRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        signature: str,
    ) -> dict[str, Any]:
        """Handle Razorpay webhook event."""
        if not self._verify_webhook_signature(payload, signature):
            raise PaymentError("Invalid webhook signature", code="INVALID_SIGNATURE")

        event_id = payload.get("id", "")
        event_type = payload.get("event", "")

        # Check idempotency
        existing = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            return {"status": "already_processed"}

        # Store webhook event
        webhook = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=json.dumps(payload),
        )
        self.db.add(webhook)

        # Process event
        if event_type == "payment.captured":
            await self._handle_payment_captured(payload)
        elif event_type == "payment.failed":
            await self._handle_payment_failed(payload)
        elif event_type == "subscription.activated":
            await self._handle_subscription_activated(payload)
        elif event_type == "subscription.cancelled":
            await self._handle_subscription_cancelled(payload)

        await self.db.flush()
        return {"status": "processed"}

    async def _handle_payment_captured(self, payload: dict[str, Any]) -> None:
        """Handle payment.captured webhook."""
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        if order_id and payment_id:
            result = await self.db.execute(
                select(PaymentRecord).where(PaymentRecord.razorpay_order_id == order_id)
            )
            payment = result.scalar_one_or_none()
            if payment and payment.status == PaymentStatus.PENDING:
                payment.complete(payment_id, "")
                await self.db.flush()

    async def _handle_payment_failed(self, payload: dict[str, Any]) -> None:
        """Handle payment.failed webhook."""
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")

        if order_id:
            result = await self.db.execute(
                select(PaymentRecord).where(PaymentRecord.razorpay_order_id == order_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.fail()
                await self.db.flush()

    async def _handle_subscription_activated(self, payload: dict[str, Any]) -> None:
        """Handle subscription.activated webhook."""
        subscription_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        razorpay_sub_id = subscription_entity.get("id")

        if razorpay_sub_id:
            result = await self.db.execute(
                select(Subscription).where(Subscription.razorpay_subscription_id == razorpay_sub_id)
            )
            subscription = result.scalar_one_or_none()
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                await self.db.flush()

    async def _handle_subscription_cancelled(self, payload: dict[str, Any]) -> None:
        """Handle subscription.cancelled webhook."""
        subscription_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        razorpay_sub_id = subscription_entity.get("id")

        if razorpay_sub_id:
            result = await self.db.execute(
                select(Subscription).where(Subscription.razorpay_subscription_id == razorpay_sub_id)
            )
            subscription = result.scalar_one_or_none()
            if subscription:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.now(tz=UTC)
                await self.db.flush()

    def _verify_webhook_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """Verify Razorpay webhook signature."""
        if not self.webhook_secret:
            return True

        payload_str = json.dumps(payload)
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
