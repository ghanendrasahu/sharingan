"""Usage tracking service."""

from __future__ import annotations

import hashlib
from typing import Any

from app.models.usage import (
    PLAN_USAGE_LIMITS,
    UsageLimits,
    UsageRecord,
    UsageSummary,
    UsageType,
)


class UsageLimitExceededError(Exception):
    """Usage limit exceeded error."""

    def __init__(self, usage_type: UsageType, limit: int) -> None:
        super().__init__(f"Usage limit exceeded for {usage_type.value}: {limit}")
        self.usage_type = usage_type
        self.limit = limit
        self.detail = {
            "error": f"Usage limit exceeded for {usage_type.value}",
            "limit": limit,
        }


class UsageService:
    """Service for tracking and enforcing usage limits."""

    def __init__(self) -> None:
        self._records: dict[str, list[UsageRecord]] = {}

    async def record_usage(
        self,
        user_id: str,
        organization_id: str,
        usage_type: UsageType,
        quantity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        """Record a usage event."""
        record = UsageRecord(
            record_id=f"usage_{hashlib.md5(f'{user_id}{usage_type.value}'.encode(), usedforsecurity=False).hexdigest()[:12]}",
            user_id=user_id,
            organization_id=organization_id,
            usage_type=usage_type,
            quantity=quantity,
            metadata=metadata or {},
        )

        # Store record
        if organization_id not in self._records:
            self._records[organization_id] = []
        self._records[organization_id].append(record)

        return record

    async def check_usage_limit(
        self,
        user_id: str,
        organization_id: str,
        usage_type: UsageType,
        plan_type: str,
    ) -> tuple[bool, int, int]:
        """
        Check if user has exceeded usage limit.

        Returns:
            Tuple of (is_allowed, current_usage, limit)
        """
        limits = PLAN_USAGE_LIMITS.get(plan_type)
        if not limits:
            return True, 0, 0

        limit = self._get_limit_for_type(limits, usage_type)

        # Unlimited
        if limit == -1:
            return True, 0, -1

        # Get current usage
        current_usage = await self.get_current_usage(organization_id, usage_type)

        is_allowed = current_usage < limit
        return is_allowed, current_usage, limit

    async def get_current_usage(
        self,
        organization_id: str,
        usage_type: UsageType,
    ) -> int:
        """Get current usage count for an organization."""
        records = self._records.get(organization_id, [])
        return sum(r.quantity for r in records if r.usage_type == usage_type)

    async def get_usage_summary(
        self,
        organization_id: str,
    ) -> dict[str, int]:
        """Get usage summary for an organization."""
        records = self._records.get(organization_id, [])
        summary: dict[str, int] = {}

        for record in records:
            usage_type = record.usage_type
            if usage_type not in summary:
                summary[usage_type] = 0
            summary[usage_type] += record.quantity

        return summary

    async def get_usage_by_period(
        self,
        organization_id: str,
        start_date: str,
        end_date: str,
    ) -> list[UsageSummary]:
        """Get usage summary for a specific period."""
        records = self._records.get(organization_id, [])
        usage_by_type: dict[UsageType, int] = {}

        for record in records:
            if start_date <= record.created_at <= end_date:
                if record.usage_type not in usage_by_type:
                    usage_by_type[record.usage_type] = 0
                usage_by_type[record.usage_type] += record.quantity

        summaries = []
        for usage_type, total in usage_by_type.items():
            summaries.append(
                UsageSummary(
                    usage_type=usage_type,
                    total_quantity=total,
                    period_start=start_date,
                    period_end=end_date,
                )
            )

        return summaries

    async def enforce_limit(
        self,
        user_id: str,
        organization_id: str,
        usage_type: UsageType,
        plan_type: str,
    ) -> UsageRecord:
        """Check limit and record usage if allowed."""
        is_allowed, _current, limit = await self.check_usage_limit(
            user_id, organization_id, usage_type, plan_type
        )

        if not is_allowed:
            raise UsageLimitExceededError(usage_type, limit)

        return await self.record_usage(user_id, organization_id, usage_type)

    def _get_limit_for_type(self, limits: UsageLimits, usage_type: UsageType) -> int:
        """Get limit for a specific usage type."""
        mapping = {
            UsageType.DOCUMENT_UPLOAD: limits.document_upload_limit,
            UsageType.AI_ANALYSIS: limits.ai_analysis_limit,
            UsageType.QA_REQUEST: limits.qa_request_limit,
            UsageType.REPORT_GENERATION: limits.report_generation_limit,
            UsageType.SEMANTIC_SEARCH: limits.semantic_search_limit,
            UsageType.STORAGE_MB: limits.storage_mb_limit,
        }
        return mapping.get(usage_type, 0)


usage_service = UsageService()
