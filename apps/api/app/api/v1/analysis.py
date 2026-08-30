"""Analysis API endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
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

logger = logging.getLogger(__name__)

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


class QuestionRequest(BaseModel):
    """Request to ask a question about a document."""

    question: str = Field(..., min_length=1, description="Question about the document")


class CitationResponse(BaseModel):
    """Citation in answer."""

    clause_id: str
    clause_type: str
    text: str
    confidence: float


class AnswerResponse(BaseModel):
    """Response to document question."""

    question: str
    answer: str
    confidence: float
    citations: list[CitationResponse] = Field(default_factory=list)
    disclaimer: str = "This is AI-generated analysis, not legal advice."


@router.post("/documents/{document_id}/ask", response_model=AnswerResponse)
async def ask_document_question(
    document_id: UUID,
    request: QuestionRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AnswerResponse:
    """Ask a question about a document.

    Returns a document-grounded answer with citations to specific clauses.
    """
    from app.models.document import DocumentClause, DocumentStatus

    # Verify document exists
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

    if document.status != DocumentStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed before asking questions",
        )

    # Get clauses
    clauses_result = await db.execute(
        select(DocumentClause)
        .where(DocumentClause.document_id == document_id)
        .order_by(DocumentClause.clause_index)
    )
    clauses = list(clauses_result.scalars().all())

    if not clauses:
        return AnswerResponse(
            question=request.question,
            answer="No clauses found in this document. The document may not have been properly processed.",
            confidence=0.0,
        )

    # Build context from clauses
    context_parts = []
    for clause in clauses[:30]:  # Limit to 30 clauses
        context_parts.append(
            f"[{clause.clause_type}] (Clause {clause.clause_id}):\n{clause.content[:500]}"
        )
    context = "\n\n".join(context_parts)

    # Call LLM for answer
    prompt = f"""Answer the question based ONLY on the document content provided.
If the document doesn't contain information to answer, say "I cannot find information about this in the document."
Always cite which clause(s) you used.

DOCUMENT CLAUSES:
{context}

QUESTION: {request.question}

Provide:
1. A direct answer (2-3 sentences max)
2. Which clause(s) support your answer
3. Your confidence level (0.0 to 1.0)
"""
    try:
        from app.services.llm import get_llm_client

        llm = get_llm_client()
        response = await llm.complete(prompt)
        answer_text = response.get("text", "Unable to generate answer")
        confidence = response.get("confidence", 0.5)

        # Find relevant citations
        citations = []
        for clause in clauses:
            if any(
                keyword in clause.content.lower()
                for keyword in request.question.lower().split()
                if len(keyword) > 3
            ):
                citations.append(
                    CitationResponse(
                        clause_id=clause.clause_id,
                        clause_type=clause.clause_type,
                        text=clause.content[:200],
                        confidence=0.7,
                    )
                )
                if len(citations) >= 3:
                    break

    except Exception:
        logger.exception("Q&A LLM call failed")
        answer_text = "I'm unable to answer this question right now. Please try again later."
        confidence = 0.0
        citations = []

    return AnswerResponse(
        question=request.question,
        answer=answer_text,
        confidence=confidence,
        citations=citations,
    )
