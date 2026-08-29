"""Usage API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from app.models.usage import UsageType
from app.schemas.usage import (
    CheckLimitRequest,
    CheckLimitResponse,
    CurrentUsageResponse,
    RecordUsageRequest,
    RecordUsageResponse,
    UsageOverviewResponse,
)
from app.services.usage import usage_service

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/overview", response_model=UsageOverviewResponse)
async def get_usage_overview(
    current_user: CurrentUser,
) -> UsageOverviewResponse:
    """Get current usage overview for the organization."""
    summary = await usage_service.get_usage_summary(str(current_user.organization_id))

    usage_responses = []
    for usage_type_str, _total in summary.items():
        try:
            usage_type = UsageType(usage_type_str)
        except ValueError:
            continue

        _is_allowed, current, limit = await usage_service.check_usage_limit(
            str(current_user.id),
            str(current_user.organization_id),
            usage_type,
            "free",  # TODO: Get from subscription
        )

        usage_responses.append(
            CurrentUsageResponse(
                usage_type=usage_type_str,
                current=current,
                limit=limit,
                remaining=max(0, limit - current) if limit != -1 else -1,
            )
        )

    return UsageOverviewResponse(
        organization_id=str(current_user.organization_id),
        plan_type="free",
        usage=usage_responses,
    )


@router.post("/record", response_model=RecordUsageResponse)
async def record_usage(
    request: RecordUsageRequest,
    current_user: CurrentUser,
) -> RecordUsageResponse:
    """Record usage for the current user."""
    try:
        usage_type = UsageType(request.usage_type)
    except ValueError:
        usage_type = UsageType.AI_ANALYSIS

    record = await usage_service.record_usage(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        usage_type=usage_type,
        quantity=request.quantity,
        metadata=request.metadata,
    )

    return RecordUsageResponse(
        record_id=record.record_id,
        usage_type=record.usage_type,
        quantity=record.quantity,
        recorded_at=record.created_at,
    )


@router.post("/check-limit", response_model=CheckLimitResponse)
async def check_usage_limit(
    request: CheckLimitRequest,
    current_user: CurrentUser,
) -> CheckLimitResponse:
    """Check if user has exceeded usage limit."""
    try:
        usage_type = UsageType(request.usage_type)
    except ValueError:
        usage_type = UsageType.AI_ANALYSIS

    is_allowed, current, limit = await usage_service.check_usage_limit(
        str(current_user.id),
        str(current_user.organization_id),
        usage_type,
        "free",  # TODO: Get from subscription
    )

    return CheckLimitResponse(
        usage_type=usage_type,
        is_allowed=is_allowed,
        current=current,
        limit=limit,
        remaining=max(0, limit - current) if limit != -1 else -1,
    )
