"""Usage API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UsageRecordResponse(BaseModel):
    """Single usage record response."""

    record_id: str
    user_id: str
    organization_id: str
    usage_type: str
    quantity: int = 1
    created_at: str


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""

    usage_type: str
    total_quantity: int
    period_start: str
    period_end: str


class UsageLimitsResponse(BaseModel):
    """Usage limits response."""

    plan_type: str
    limits: dict[str, int]


class CurrentUsageResponse(BaseModel):
    """Current usage status response."""

    usage_type: str
    current: int
    limit: int
    remaining: int


class UsageOverviewResponse(BaseModel):
    """Complete usage overview response."""

    organization_id: str
    plan_type: str
    usage: list[CurrentUsageResponse]
    total_documents: int = 0
    total_analyses: int = 0
    total_storage_mb: float = 0.0


class RecordUsageRequest(BaseModel):
    """Request to record usage."""

    usage_type: str = Field(..., description="Type of usage")
    quantity: int = Field(default=1, ge=1, description="Quantity to record")
    metadata: dict[str, str] | None = Field(default=None, description="Additional metadata")


class RecordUsageResponse(BaseModel):
    """Response after recording usage."""

    record_id: str
    usage_type: str
    quantity: int
    recorded_at: str


class CheckLimitRequest(BaseModel):
    """Request to check usage limit."""

    usage_type: str = Field(..., description="Type of usage to check")


class CheckLimitResponse(BaseModel):
    """Response for limit check."""

    usage_type: str
    is_allowed: bool
    current: int
    limit: int
    remaining: int
