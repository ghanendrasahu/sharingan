"""Analysis API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_config import celery_app
from app.core.database import get_db
from app.models.analysis import AnalysisResult, AnalysisRisk, AnalysisStatus
from app.models.document import Document
from app.models.organization import MemberRole
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResultResponse,
    AnalysisStatusResponse,
    RiskFindingResponse,
)
from app.tasks.analysis import analyze_document_task

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/analysis", tags=["analysis"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _verify_document_access(
    document_id: UUID,
    organization_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession,
) -> Document:
    """Verify user has access to the document."""
    from app.api.deps import RequireRole

    # Check organization membership
    membership_check = RequireRole(
        MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER, MemberRole.VIEWER
    )
    await membership_check(organization_id, current_user, db)

    # Get document
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None),
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post("/analyze", response_model=AnalysisStatusResponse)
async def start_analysis(
    request: AnalysisRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AnalysisStatusResponse:
    """Start document analysis.

    Triggers a background task to analyze the document.
    Use the task_id to poll for status and results.
    """
    document_id = UUID(request.document_id)

    # Verify document exists and user has access
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None),
        )
    )
    document = doc_result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check document is processed
    from app.models.document import DocumentStatus

    if document.status != DocumentStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document must be processed before analysis. Current status: {document.status}",
        )

    # Trigger Celery task
    task = analyze_document_task.delay(  # type: ignore[reportCallIssue]
        document_id=str(document_id),
        analysis_type=request.analysis_type,
        user_id=str(current_user.id),
        organization_id=str(document.organization_id),
    )

    return AnalysisStatusResponse(
        task_id=task.id,
        document_id=str(document_id),
        status="pending",
        progress=0.0,
        message="Analysis task created",
        created_at=document.created_at.isoformat() if document.created_at else "",
    )


@router.get("/status/{task_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    task_id: str,
    current_user: CurrentUser,
) -> AnalysisStatusResponse:
    """Get analysis task status.

    Returns the current status and progress of an analysis task.
    """
    # Query Celery for task status
    result = celery_app.AsyncResult(task_id)

    # Map Celery states to our status
    status_map = {
        "PENDING": "pending",
        "STARTED": "processing",
        "PROCESSING": "processing",
        "COMPLETED": "completed",
        "FAILED": "failed",
        "RETRY": "retrying",
        "CANCELLED": "cancelled",
    }

    task_status = status_map.get(result.state, "unknown")
    progress = 0.0
    message = ""
    error = None

    if result.info:
        if isinstance(result.info, dict):
            progress = result.info.get("progress", 0.0)
            message = result.info.get("message", "")
            error = result.info.get("error")
        elif isinstance(result.info, str):
            error = result.info

    if result.state == "COMPLETED":
        progress = 1.0
        message = "Analysis completed"
    elif result.state == "FAILED":
        error = str(result.info) if result.info else "Task failed"

    return AnalysisStatusResponse(
        task_id=task_id,
        document_id=result.info.get("document_id", "") if isinstance(result.info, dict) else "",
        status=task_status,
        progress=progress,
        message=message,
        created_at="",
        error=error,
    )


@router.get("/result/{document_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AnalysisResultResponse:
    """Get analysis result for a document.

    Returns the full analysis result including risks, terms, and recommendations.
    """
    # Get latest completed analysis for this document
    result = await db.execute(
        select(AnalysisResult)
        .where(
            AnalysisResult.document_id == document_id,
            AnalysisResult.status == AnalysisStatus.COMPLETED,
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed analysis found for this document",
        )

    # Get risk findings
    risks_result = await db.execute(
        select(AnalysisRisk)
        .where(AnalysisRisk.analysis_id == analysis.id)
        .order_by(AnalysisRisk.confidence.desc())
    )
    risks = list(risks_result.scalars().all())

    # Parse recommendations
    import json

    recommendations = []
    if analysis.recommendations:
        try:
            recommendations = json.loads(analysis.recommendations)
        except (json.JSONDecodeError, TypeError):
            recommendations = []

    return AnalysisResultResponse(
        analysis_id=str(analysis.id),
        document_id=str(analysis.document_id),
        analysis_type=analysis.analysis_type,
        summary=analysis.summary or "",
        overall_risk_score=analysis.overall_risk_score,
        risk_findings=[
            RiskFindingResponse(
                risk_id=risk.risk_id,
                title=risk.title,
                description=risk.description or "",
                severity=risk.severity,
                clause_reference=risk.clause_reference,
                recommendation=risk.recommendation or "",
                confidence=risk.confidence,
            )
            for risk in risks
        ],
        key_terms=[],  # Key terms not stored in DB yet
        recommendations=recommendations,
        high_risk_count=analysis.high_risk_count,
        medium_risk_count=analysis.medium_risk_count,
        low_risk_count=analysis.low_risk_count,
        processing_time_ms=analysis.processing_time_ms,
    )


@router.get("/risks/{analysis_id}", response_model=list[RiskFindingResponse])
async def get_analysis_risks(
    analysis_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[RiskFindingResponse]:
    """Get risks for a specific analysis."""
    # Verify analysis exists
    analysis_result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == analysis_id)
    )
    analysis = analysis_result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    # Get risks
    risks_result = await db.execute(
        select(AnalysisRisk)
        .where(AnalysisRisk.analysis_id == analysis_id)
        .order_by(AnalysisRisk.confidence.desc())
    )
    risks = list(risks_result.scalars().all())

    return [
        RiskFindingResponse(
            risk_id=risk.risk_id,
            title=risk.title,
            description=risk.description or "",
            severity=risk.severity,
            clause_reference=risk.clause_reference,
            recommendation=risk.recommendation or "",
            confidence=risk.confidence,
        )
        for risk in risks
    ]


@router.delete("/cancel/{task_id}")
async def cancel_analysis(
    task_id: str,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Cancel a running analysis task."""
    # Revoke the Celery task
    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")

    return {"message": f"Task {task_id} cancelled", "task_id": task_id}
