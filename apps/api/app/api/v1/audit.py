"""Audit log API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Query

from app.models.audit import AuditEventType, AuditSeverity
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogsResponse,
    LogEventRequest,
    SecuritySummaryResponse,
)
from app.services.audit import audit_service

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/log", response_model=AuditLogResponse)
async def log_event(
    request: LogEventRequest,
    current_user: CurrentUser,
) -> AuditLogResponse:
    """Log an audit event."""
    event_type = AuditEventType(request.event_type)
    severity = AuditSeverity(request.severity) if request.severity else AuditSeverity.LOW

    log = audit_service.log_event(
        event_type=event_type,
        user_id=str(current_user.id),
        organization_id=request.organization_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        details=request.details,
        severity=severity,
    )

    return AuditLogResponse(
        log_id=log.log_id,
        event_type=log.event_type.value,
        user_id=log.user_id,
        organization_id=log.organization_id,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        details=log.details,
        severity=log.severity.value,
        created_at=log.created_at.isoformat(),
    )


@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    current_user: CurrentUser,
    organization_id: str | None = Query(None),
    event_types: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> AuditLogsResponse:
    """Get audit logs with filtering."""
    from app.models.audit import AuditLogFilter

    parsed_event_types = None
    if event_types:
        parsed_event_types = [AuditEventType(e.strip()) for e in event_types.split(",")]

    parsed_severity = AuditSeverity(severity) if severity else None

    filter_obj = AuditLogFilter(
        organization_id=organization_id or current_user.organization_id,
        event_types=parsed_event_types,
        severity=parsed_severity,
    )

    logs = audit_service.get_logs(filter_obj, limit, offset)

    return AuditLogsResponse(
        logs=[
            AuditLogResponse(
                log_id=log.log_id,
                event_type=log.event_type.value,
                user_id=log.user_id,
                organization_id=log.organization_id,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                severity=log.severity.value,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ],
        total=len(logs),
        limit=limit,
        offset=offset,
    )


@router.get("/security-summary", response_model=SecuritySummaryResponse)
async def get_security_summary(
    current_user: CurrentUser,
    organization_id: str | None = Query(None),
) -> SecuritySummaryResponse:
    """Get security summary for an organization."""
    summary = audit_service.get_security_summary(organization_id or current_user.organization_id)

    return SecuritySummaryResponse(
        total_events=summary["total_events"],
        security_events=summary["security_events"],
        high_risk_events=summary["high_risk_events"],
        event_counts=summary["event_counts"],
    )


@router.get("/high-risk")
async def get_high_risk_logs(
    current_user: CurrentUser,
    organization_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Get high-risk audit logs."""
    logs = audit_service.get_high_risk_logs(
        organization_id=organization_id or current_user.organization_id,
        limit=limit,
    )
    return [log.to_dict() for log in logs]


@router.get("/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    current_user: CurrentUser,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """Get audit logs for a specific user."""
    logs = audit_service.get_user_logs(user_id, limit, offset)
    return [log.to_dict() for log in logs]
