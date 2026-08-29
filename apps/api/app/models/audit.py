"""Audit log models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AuditEventType(StrEnum):
    """Audit event types."""

    # Authentication events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    PASSWORD_CHANGE = "password.change"
    PASSWORD_RESET = "password.reset"
    MFA_ENABLE = "mfa.enable"
    MFA_DISABLE = "mfa.disable"

    # Document events
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_VIEW = "document.view"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_DOWNLOAD = "document.download"

    # Analysis events
    ANALYSIS_START = "analysis.start"
    ANALYSIS_COMPLETE = "analysis.complete"
    ANALYSIS_FAILED = "analysis.failed"

    # Search events
    SEARCH_QUERY = "search.query"
    SEARCH_EXPORT = "search.export"

    # Report events
    REPORT_VIEW = "report.view"
    REPORT_EXPORT = "report.export"
    REPORT_DELETE = "report.delete"

    # Organization events
    ORG_CREATE = "organization.create"
    ORG_UPDATE = "organization.update"
    ORG_DELETE = "organization.delete"
    ORG_MEMBER_ADD = "organization.member.add"
    ORG_MEMBER_REMOVE = "organization.member.remove"
    ORG_MEMBER_ROLE_UPDATE = "organization.member.role.update"

    # Subscription events
    SUBSCRIPTION_CREATE = "subscription.create"
    SUBSCRIPTION_UPDATE = "subscription.update"
    SUBSCRIPTION_CANCEL = "subscription.cancel"
    PAYMENT_COMPLETE = "payment.complete"
    PAYMENT_FAILED = "payment.failed"

    # System events
    SYSTEM_ERROR = "system.error"
    RATE_LIMIT = "rate.limit"
    SECURITY_VIOLATION = "security.violation"


class AuditSeverity(StrEnum):
    """Audit event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog:
    """Audit log entry for tracking user actions."""

    def __init__(
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
    ) -> None:
        self.log_id = f"audit_{hash(f'{event_type}{user_id}{datetime.now(tz=UTC).isoformat()}') & 0xFFFFFFFF:08x}"
        self.event_type = event_type
        self.user_id = user_id
        self.organization_id = organization_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.severity = severity
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.now(tz=UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_id": self.log_id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }

    def is_high_risk(self) -> bool:
        """Check if this is a high-risk event."""
        return self.severity in (AuditSeverity.HIGH, AuditSeverity.CRITICAL)

    def is_organization_event(self) -> bool:
        """Check if this is an organization-level event."""
        return self.organization_id is not None


class AuditLogFilter:
    """Filter for querying audit logs."""

    def __init__(
        self,
        organization_id: str | None = None,
        user_id: str | None = None,
        event_types: list[AuditEventType] | None = None,
        severity: AuditSeverity | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        resource_type: str | None = None,
    ) -> None:
        self.organization_id = organization_id
        self.user_id = user_id
        self.event_types = event_types
        self.severity = severity
        self.start_date = start_date
        self.end_date = end_date
        self.resource_type = resource_type

    def matches(self, log: AuditLog) -> bool:
        """Check if a log entry matches this filter."""
        if self.organization_id and log.organization_id != self.organization_id:
            return False
        if self.user_id and log.user_id != self.user_id:
            return False
        if self.event_types and log.event_type not in self.event_types:
            return False
        if self.severity and log.severity != self.severity:
            return False
        if self.start_date and log.created_at < self.start_date:
            return False
        if self.end_date and log.created_at > self.end_date:
            return False
        return not (self.resource_type and log.resource_type != self.resource_type)
