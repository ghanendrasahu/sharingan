"""Background tasks for AI analysis."""

from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any

from celery import shared_task
from legallens_docproc.ai_analyzer import (
    AIAnalysisError,
    analyze_document_full,
    get_llm_provider,
)
from legallens_docproc.analysis_models import AnalysisType

from app.core.config import get_settings
from app.core.database import get_sync_session
from app.models.analysis import AnalysisResult, AnalysisRisk, AnalysisStatus
from app.models.document import DocumentClause
from app.models.task import TaskInfo, TaskType

settings = get_settings()


@shared_task(
    name="app.tasks.analysis.analyze_document_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="ai_analysis",
)
def analyze_document_task(
    self,
    document_id: str,
    analysis_type: str = "full_analysis",
    user_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a document using AI.

    Steps:
    1. Load document text and clauses from database
    2. Configure LLM provider
    3. Run AI analysis
    4. Store results in database
    """
    task_info = TaskInfo(
        task_id=self.request.id,
        task_type=TaskType.AI_ANALYSIS,
        document_id=document_id,
        user_id=user_id,
        organization_id=organization_id,
    )

    try:
        # Step 1: Load document data from database
        task_info.update_progress(0.05, "Loading document data...")
        _update_task_state(self, task_info)

        session = get_sync_session()
        try:
            # Get document clauses
            clauses_data = (
                session.query(DocumentClause)
                .filter(DocumentClause.document_id == document_id)
                .all()
            )

            # Get document text from pages
            from app.models.document import DocumentPage

            pages = (
                session.query(DocumentPage)
                .filter(DocumentPage.document_id == document_id)
                .order_by(DocumentPage.page_number)
                .all()
            )
            document_text = "\n\n".join(p.text for p in pages if p.text)

            if not document_text.strip():
                raise ValueError("No text content found for document")

            # Create analysis record
            analysis = AnalysisResult(
                document_id=document_id,
                organization_id=organization_id,
                analysis_type=analysis_type,
                status=AnalysisStatus.PROCESSING,
            )
            session.add(analysis)
            session.commit()
            analysis_id = str(analysis.id)
        finally:
            session.close()

        # Step 2: Configure LLM provider
        task_info.update_progress(0.1, "Configuring AI provider...")
        _update_task_state(self, task_info)

        provider_name = settings.LLM_PROVIDER
        api_key = settings.LLM_API_KEY or settings.GROQ_API_KEY
        model = settings.LLM_MODEL if provider_name == "openai" else settings.GROQ_MODEL

        if not api_key:
            # Fall back to mock provider if no API key configured
            provider_name = "mock"
            provider = get_llm_provider(provider_name)
        else:
            provider = get_llm_provider(provider_name, api_key=api_key, model=model)

        # Step 3: Convert clauses to legallens_docproc format
        task_info.update_progress(0.15, "Preparing clauses for analysis...")
        _update_task_state(self, task_info)

        from legallens_docproc.clause_models import Clause as DocProcClause
        from legallens_docproc.clause_models import ClauseRiskLevel, ClauseType

        docproc_clauses = []
        for c in clauses_data:
            try:
                clause_type = ClauseType(c.clause_type)
            except ValueError:
                clause_type = ClauseType.OTHER

            risk_level = None
            if c.risk_level:
                try:
                    risk_level = ClauseRiskLevel(c.risk_level)
                except ValueError:
                    risk_level = None

            docproc_clauses.append(
                DocProcClause(
                    clause_id=c.clause_id,
                    text=c.text,
                    clause_type=clause_type,
                    risk_level=risk_level,
                    page_number=c.page_number,
                    char_start=c.char_start,
                    char_end=c.char_end,
                    confidence=c.confidence,
                )
            )

        # Step 4: Run AI analysis
        task_info.update_progress(0.2, "Running AI analysis...")
        _update_task_state(self, task_info)

        analysis_enum = AnalysisType(analysis_type)
        result = asyncio.run(
            analyze_document_full(
                document_id=document_id,
                document_text=document_text,
                clauses=docproc_clauses,
                provider=provider,
                analysis_type=analysis_enum,
            )
        )

        # Step 5: Store results in database
        task_info.update_progress(0.8, "Storing analysis results...")
        _update_task_state(self, task_info)

        session = get_sync_session()
        try:
            existing_analysis = (
                session.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
            )
            assert existing_analysis is not None, f"Analysis {analysis_id} not found"

            existing_analysis.status = AnalysisStatus.COMPLETED
            existing_analysis.summary = result.summary
            existing_analysis.overall_risk_score = result.overall_risk_score
            existing_analysis.high_risk_count = result.high_risk_count
            existing_analysis.medium_risk_count = result.medium_risk_count
            existing_analysis.low_risk_count = result.low_risk_count
            existing_analysis.recommendations = json.dumps(result.recommendations)
            existing_analysis.model_used = result.model_used
            existing_analysis.processing_time_ms = result.processing_time_ms
            existing_analysis.error = result.error

            # Store individual risk findings
            for risk in result.risk_findings:
                db_risk = AnalysisRisk(
                    analysis_id=existing_analysis.id,
                    risk_id=risk.risk_id,
                    title=risk.title,
                    description=risk.description,
                    severity=risk.severity.value,
                    clause_reference=risk.clause_reference,
                    recommendation=risk.recommendation,
                    confidence=risk.confidence,
                )
                session.add(db_risk)

            session.commit()
        finally:
            session.close()

        # Complete
        task_info.update_progress(1.0, "Analysis complete")
        task_info.complete(
            result={
                "analysis_id": analysis_id,
                "document_id": document_id,
                "analysis_type": analysis_type,
                "risk_score": result.overall_risk_score,
                "risks_found": len(result.risk_findings),
                "high_risk_count": result.high_risk_count,
                "medium_risk_count": result.medium_risk_count,
                "low_risk_count": result.low_risk_count,
                "processing_time_ms": result.processing_time_ms or 0,
            }
        )

        return task_info.to_dict()

    except AIAnalysisError as e:
        # Mark analysis as failed
        _mark_analysis_failed(document_id, str(e))
        task_info.fail(error=str(e), traceback=traceback.format_exc())
        raise self.retry(exc=e)  # noqa: B904

    except Exception as e:
        _mark_analysis_failed(document_id, str(e))
        task_info.fail(error=str(e), traceback=traceback.format_exc())
        raise self.retry(exc=e)  # noqa: B904


def _mark_analysis_failed(document_id: str, error: str) -> None:
    """Mark analysis as failed in database."""
    try:
        session = get_sync_session()
        try:
            analysis = (
                session.query(AnalysisResult)
                .filter(
                    AnalysisResult.document_id == document_id,
                    AnalysisResult.status == AnalysisStatus.PROCESSING,
                )
                .order_by(AnalysisResult.created_at.desc())
                .first()
            )
            if analysis is not None:
                analysis.status = AnalysisStatus.FAILED
                analysis.error = error
                session.commit()
        finally:
            session.close()
    except Exception:
        pass  # Don't mask original error


def _update_task_state(task, task_info: TaskInfo) -> None:
    """Update task state for monitoring."""
    task.update_state(
        state=task_info.status,
        meta=task_info.to_dict(),
    )
