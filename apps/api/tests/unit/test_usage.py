"""Unit tests for usage tracking models and service."""

import pytest

from app.models.usage import (
    PLAN_USAGE_LIMITS,
    UsageLimits,
    UsageRecord,
    UsageType,
)
from app.schemas.usage import (
    RecordUsageResponse,
    UsageOverviewResponse,
)
from app.services.usage import UsageService


def test_usage_type_enum():
    """Test usage type enum values."""
    assert UsageType.DOCUMENT_UPLOAD == "document_upload"
    assert UsageType.AI_ANALYSIS == "ai_analysis"
    assert UsageType.QA_REQUEST == "qa_request"
    assert UsageType.REPORT_GENERATION == "report_generation"
    assert UsageType.SEMANTIC_SEARCH == "semantic_search"


def test_usage_record_creation():
    """Test usage record creation."""
    record = UsageRecord(
        record_id="usage_123",
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
        quantity=1,
    )
    assert record.user_id == "user_123"
    assert record.usage_type == UsageType.AI_ANALYSIS
    assert record.created_at != ""


def test_usage_record_to_dict():
    """Test usage record to_dict method."""
    record = UsageRecord(
        record_id="usage_123",
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
    )
    data = record.to_dict()
    assert data["record_id"] == "usage_123"
    assert data["usage_type"] == "ai_analysis"


def test_usage_limits():
    """Test usage limits."""
    limits = UsageLimits(
        plan_type="starter",
        document_upload_limit=100,
        ai_analysis_limit=50,
        qa_request_limit=200,
        report_generation_limit=50,
        semantic_search_limit=200,
        storage_mb_limit=1024,
    )
    assert limits.plan_type == "starter"
    assert limits.ai_analysis_limit == 50


def test_plan_usage_limits():
    """Test predefined plan limits."""
    assert "free" in PLAN_USAGE_LIMITS
    assert "starter" in PLAN_USAGE_LIMITS
    assert "professional" in PLAN_USAGE_LIMITS
    assert "enterprise" in PLAN_USAGE_LIMITS

    free_limits = PLAN_USAGE_LIMITS["free"]
    assert free_limits.ai_analysis_limit == 5

    enterprise_limits = PLAN_USAGE_LIMITS["enterprise"]
    assert enterprise_limits.ai_analysis_limit == -1  # Unlimited


@pytest.mark.asyncio
async def test_usage_service_record():
    """Test usage service record functionality."""
    service = UsageService()

    record = await service.record_usage(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
    )

    assert record.user_id == "user_123"
    assert record.usage_type == UsageType.AI_ANALYSIS


@pytest.mark.asyncio
async def test_usage_service_check_limit():
    """Test usage service limit checking."""
    service = UsageService()

    # Initially should be allowed
    is_allowed, current, limit = await service.check_usage_limit(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
        plan_type="free",
    )

    assert is_allowed is True
    assert current == 0
    assert limit == 5


@pytest.mark.asyncio
async def test_usage_service_enforce_limit():
    """Test usage service limit enforcement."""
    service = UsageService()

    # Record usage up to limit
    for _ in range(4):
        await service.record_usage(
            user_id="user_123",
            organization_id="org_123",
            usage_type=UsageType.AI_ANALYSIS,
        )

    # Should still be allowed
    is_allowed, current, _limit = await service.check_usage_limit(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
        plan_type="free",
    )

    assert is_allowed is True
    assert current == 4


@pytest.mark.asyncio
async def test_usage_service_unlimited():
    """Test unlimited usage for enterprise plan."""
    service = UsageService()

    is_allowed, _current, limit = await service.check_usage_limit(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
        plan_type="enterprise",
    )

    assert is_allowed is True
    assert limit == -1


@pytest.mark.asyncio
async def test_usage_service_summary():
    """Test usage service summary."""
    service = UsageService()

    await service.record_usage(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.AI_ANALYSIS,
    )
    await service.record_usage(
        user_id="user_123",
        organization_id="org_123",
        usage_type=UsageType.QA_REQUEST,
        quantity=3,
    )

    summary = await service.get_usage_summary("org_123")
    assert summary.get("ai_analysis") == 1
    assert summary.get("qa_request") == 3


def test_usage_overview_response():
    """Test usage overview response schema."""
    response = UsageOverviewResponse(
        organization_id="org_123",
        plan_type="free",
        usage=[],
    )
    assert response.organization_id == "org_123"


def test_record_usage_response():
    """Test record usage response schema."""
    response = RecordUsageResponse(
        record_id="usage_123",
        usage_type="ai_analysis",
        quantity=1,
        recorded_at="2024-01-01T00:00:00Z",
    )
    assert response.record_id == "usage_123"
