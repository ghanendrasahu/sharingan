"""Usage tracking models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class UsageType(StrEnum):
    """Types of usage to track."""

    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_PROCESSING = "document_processing"
    AI_ANALYSIS = "ai_analysis"
    QA_REQUEST = "qa_request"
    REPORT_GENERATION = "report_generation"
    SEMANTIC_SEARCH = "semantic_search"
    STORAGE_MB = "storage_mb"


@dataclass
class UsageRecord:
    """Single usage record."""

    record_id: str
    user_id: str
    organization_id: str
    usage_type: UsageType
    quantity: int = 1
    metadata: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(tz=UTC).isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "usage_type": self.usage_type,
            "quantity": self.quantity,
            "created_at": self.created_at,
        }


@dataclass
class UsageSummary:
    """Usage summary for a period."""

    usage_type: UsageType
    total_quantity: int
    period_start: str
    period_end: str


@dataclass
class UsageLimits:
    """Usage limits for a plan."""

    plan_type: str
    document_upload_limit: int
    ai_analysis_limit: int
    qa_request_limit: int
    report_generation_limit: int
    semantic_search_limit: int
    storage_mb_limit: int


# Predefined usage limits per plan
PLAN_USAGE_LIMITS = {
    "free": UsageLimits(
        plan_type="free",
        document_upload_limit=10,
        ai_analysis_limit=5,
        qa_request_limit=10,
        report_generation_limit=5,
        semantic_search_limit=20,
        storage_mb_limit=100,
    ),
    "starter": UsageLimits(
        plan_type="starter",
        document_upload_limit=100,
        ai_analysis_limit=50,
        qa_request_limit=200,
        report_generation_limit=50,
        semantic_search_limit=200,
        storage_mb_limit=1024,
    ),
    "professional": UsageLimits(
        plan_type="professional",
        document_upload_limit=500,
        ai_analysis_limit=200,
        qa_request_limit=1000,
        report_generation_limit=200,
        semantic_search_limit=1000,
        storage_mb_limit=5120,
    ),
    "enterprise": UsageLimits(
        plan_type="enterprise",
        document_upload_limit=-1,  # Unlimited
        ai_analysis_limit=-1,
        qa_request_limit=-1,
        report_generation_limit=-1,
        semantic_search_limit=-1,
        storage_mb_limit=-1,
    ),
}
