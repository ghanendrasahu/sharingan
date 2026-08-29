"""Audit log API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LogEventRequest(BaseModel):
    """Request to log an audit event."""

    event_type: str = Field(..., description="Event type")
    organization_id: str | None = Field(None, description="Organization ID")
    resource_type: str | None = Field(None, description="Resource type")
    resource_id: str | None = Field(None, description="Resource ID")
    details: dict[str, Any] | None = Field(None, description="Additional details")
    severity: str | None = Field(None, description="Event severity")


class AuditLogResponse(BaseModel):
    """Audit log response."""

    log_id: str = Field(..., description="Log ID")
    event_type: str = Field(..., description="Event type")
    user_id: str | None = Field(None, description="User ID")
    organization_id: str | None = Field(None, description="Organization ID")
    resource_type: str | None = Field(None, description="Resource type")
    resource_id: str | None = Field(None, description="Resource ID")
    details: dict[str, Any] | None = Field(None, description="Additional details")
    severity: str = Field(..., description="Event severity")
    created_at: str = Field(..., description="Creation timestamp")


class AuditLogsResponse(BaseModel):
    """Audit logs list response."""

    logs: list[AuditLogResponse] = Field(..., description="Audit logs")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page limit")
    offset: int = Field(..., description="Page offset")


class SecuritySummaryResponse(BaseModel):
    """Security summary response."""

    total_events: int = Field(..., description="Total events")
    security_events: int = Field(..., description="Security events count")
    high_risk_events: int = Field(..., description="High-risk events count")
    event_counts: dict[str, int] = Field(..., description="Events by type")
