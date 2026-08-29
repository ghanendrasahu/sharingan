"""Unit tests for audit log service."""

import pytest

from app.models.audit import (
    AuditEventType,
    AuditLog,
    AuditLogFilter,
    AuditSeverity,
)
from app.services.audit import AuditService


@pytest.fixture
def audit_service() -> AuditService:
    """Create an audit service instance."""
    return AuditService()


def test_audit_event_type_enum():
    """Test audit event type enum values."""
    assert AuditEventType.USER_LOGIN == "user.login"
    assert AuditEventType.DOCUMENT_UPLOAD == "document.upload"
    assert AuditEventType.ANALYSIS_COMPLETE == "analysis.complete"


def test_audit_severity_enum():
    """Test audit severity enum values."""
    assert AuditSeverity.LOW == "low"
    assert AuditSeverity.MEDIUM == "medium"
    assert AuditSeverity.HIGH == "high"
    assert AuditSeverity.CRITICAL == "critical"


def test_audit_log_creation():
    """Test audit log creation."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    assert log.event_type == AuditEventType.USER_LOGIN
    assert log.user_id == "user_123"
    assert log.organization_id == "org_123"
    assert log.severity == AuditSeverity.LOW


def test_audit_log_high_risk():
    """Test high-risk event detection."""
    log = AuditLog(
        event_type=AuditEventType.SECURITY_VIOLATION,
        severity=AuditSeverity.CRITICAL,
    )
    assert log.is_high_risk() is True


def test_audit_log_not_high_risk():
    """Test non-high-risk event detection."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        severity=AuditSeverity.LOW,
    )
    assert log.is_high_risk() is False


def test_audit_log_organization_event():
    """Test organization event detection."""
    log = AuditLog(
        event_type=AuditEventType.ORG_CREATE,
        organization_id="org_123",
    )
    assert log.is_organization_event() is True


def test_audit_log_not_organization_event():
    """Test non-organization event detection."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
    )
    assert log.is_organization_event() is False


def test_audit_log_to_dict():
    """Test audit log to dictionary conversion."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
        details={"ip": "127.0.0.1"},
    )
    log_dict = log.to_dict()
    assert log_dict["event_type"] == "user.login"
    assert log_dict["user_id"] == "user_123"
    assert log_dict["details"]["ip"] == "127.0.0.1"


def test_audit_log_filter_matches():
    """Test audit log filter matching."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    filter_obj = AuditLogFilter(
        organization_id="org_123",
        user_id="user_123",
    )
    assert filter_obj.matches(log) is True


def test_audit_log_filter_no_match():
    """Test audit log filter non-matching."""
    log = AuditLog(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    filter_obj = AuditLogFilter(
        organization_id="org_456",
    )
    assert filter_obj.matches(log) is False


@pytest.mark.asyncio
async def test_audit_service_log_event(audit_service: AuditService):
    """Test logging an event."""
    log = audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    assert log.event_type == AuditEventType.USER_LOGIN
    assert log.user_id == "user_123"


@pytest.mark.asyncio
async def test_audit_service_get_logs(audit_service: AuditService):
    """Test getting audit logs."""
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
    )
    audit_service.log_event(
        event_type=AuditEventType.DOCUMENT_UPLOAD,
        user_id="user_123",
    )

    logs = audit_service.get_logs()
    assert len(logs) == 2


@pytest.mark.asyncio
async def test_audit_service_get_organization_logs(audit_service: AuditService):
    """Test getting organization audit logs."""
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_456",
        organization_id="org_456",
    )

    logs = audit_service.get_organization_logs("org_123")
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_audit_service_get_high_risk_logs(audit_service: AuditService):
    """Test getting high-risk audit logs."""
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        severity=AuditSeverity.LOW,
    )
    audit_service.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        user_id="user_123",
        severity=AuditSeverity.CRITICAL,
    )

    logs = audit_service.get_high_risk_logs()
    assert len(logs) == 1
    assert logs[0].severity == AuditSeverity.CRITICAL


@pytest.mark.asyncio
async def test_audit_service_get_event_counts(audit_service: AuditService):
    """Test getting event counts."""
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
    )
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
    )
    audit_service.log_event(
        event_type=AuditEventType.DOCUMENT_UPLOAD,
        user_id="user_123",
    )

    counts = audit_service.get_event_counts()
    assert counts["user.login"] == 2
    assert counts["document.upload"] == 1


@pytest.mark.asyncio
async def test_audit_service_get_security_summary(audit_service: AuditService):
    """Test getting security summary."""
    audit_service.log_event(
        event_type=AuditEventType.USER_LOGIN,
        user_id="user_123",
        organization_id="org_123",
    )
    audit_service.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        user_id="user_123",
        organization_id="org_123",
        severity=AuditSeverity.CRITICAL,
    )

    summary = audit_service.get_security_summary("org_123")
    assert summary["total_events"] == 2
    assert summary["security_events"] == 1
    assert summary["high_risk_events"] == 1
