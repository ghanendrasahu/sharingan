"""Audit log service for tracking user actions."""

from __future__ import annotations

from typing import Any

from app.models.audit import (
    AuditEventType,
    AuditLog,
    AuditLogFilter,
    AuditSeverity,
)


class AuditService:
    """Service for managing audit logs."""

    def __init__(self) -> None:
        self._logs: list[AuditLog] = []

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        organization_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log an audit event."""
        log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._logs.append(log)
        return log

    def get_logs(
        self,
        filter_obj: AuditLogFilter | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with optional filtering."""
        if filter_obj:
            filtered = [log for log in self._logs if filter_obj.matches(log)]
        else:
            filtered = self._logs.copy()

        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[offset : offset + limit]

    def get_organization_logs(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific organization."""
        filter_obj = AuditLogFilter(organization_id=organization_id)
        return self.get_logs(filter_obj, limit, offset)

    def get_user_logs(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific user."""
        filter_obj = AuditLogFilter(user_id=user_id)
        return self.get_logs(filter_obj, limit, offset)

    def get_high_risk_logs(
        self,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get high-risk audit logs."""
        high_risk_severities = [AuditSeverity.HIGH, AuditSeverity.CRITICAL]
        logs = [
            log
            for log in self._logs
            if log.severity in high_risk_severities
            and (organization_id is None or log.organization_id == organization_id)
        ]
        logs.sort(key=lambda x: x.created_at, reverse=True)
        return logs[:limit]

    def get_event_counts(
        self,
        organization_id: str | None = None,
    ) -> dict[str, int]:
        """Get count of events by type."""
        counts: dict[str, int] = {}
        for log in self._logs:
            if organization_id and log.organization_id != organization_id:
                continue
            event_name = log.event_type.value
            counts[event_name] = counts.get(event_name, 0) + 1
        return counts

    def get_security_summary(
        self,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Get security summary for an organization."""
        logs = self.get_organization_logs(organization_id) if organization_id else self._logs

        security_events = [
            AuditEventType.USER_LOGIN,
            AuditEventType.USER_LOGOUT,
            AuditEventType.PASSWORD_CHANGE,
            AuditEventType.PASSWORD_RESET,
            AuditEventType.MFA_ENABLE,
            AuditEventType.MFA_DISABLE,
        ]

        security_logs = [log for log in logs if log.event_type in security_events]

        return {
            "total_events": len(logs),
            "security_events": len(security_logs),
            "high_risk_events": len(self.get_high_risk_logs(organization_id)),
            "event_counts": self.get_event_counts(organization_id),
        }


audit_service = AuditService()
