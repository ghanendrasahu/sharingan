"""Report API endpoints for document analysis reports."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.analysis import AnalysisResult, AnalysisRisk, AnalysisStatus
from app.models.document import Document
from app.models.report import Report, ReportStatus
from app.schemas.report import (
    ReportDeleteResponse,
    ReportDetailResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportGenerateRequest,
    ReportListResponse,
    ReportSectionResponse,
    ReportStatsResponse,
    RiskSummaryResponse,
)

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/reports", tags=["reports"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _build_report_detail(report: Report, sections_json: str | None = None) -> ReportDetailResponse:
    """Build ReportDetailResponse from Report model."""
    sections = []
    if report.sections:
        try:
            sections_data = json.loads(report.sections)
            sections = [
                ReportSectionResponse(
                    title=s.get("title", ""),
                    content=s.get("content", ""),
                    section_type=s.get("section_type", "text"),
                )
                for s in sections_data
            ]
        except (json.JSONDecodeError, TypeError):
            pass

    risk_summary = None
    if report.risk_summary:
        try:
            rs = json.loads(report.risk_summary)
            risk_summary = RiskSummaryResponse(
                total_risks=rs.get("total_risks", 0),
                critical_count=rs.get("critical_count", 0),
                high_count=rs.get("high_count", 0),
                medium_count=rs.get("medium_count", 0),
                low_count=rs.get("low_count", 0),
                overall_risk_score=rs.get("overall_risk_score", 0.0),
                risk_level=rs.get("risk_level", "low"),
            )
        except (json.JSONDecodeError, TypeError):
            pass

    key_terms = []
    if report.key_terms:
        import contextlib

        with contextlib.suppress(json.JSONDecodeError, TypeError):
            key_terms = json.loads(report.key_terms)

    recommendations = []
    if report.recommendations:
        import contextlib

        with contextlib.suppress(json.JSONDecodeError, TypeError):
            recommendations = json.loads(report.recommendations)

    return ReportDetailResponse(
        report_id=str(report.id),
        document_id=str(report.document_id),
        report_type=report.report_type,
        title=report.title,
        executive_summary=report.executive_summary or "",
        sections=sections,
        risk_summary=risk_summary,
        key_terms=key_terms,
        recommendations=recommendations,
        generated_at=report.created_at.isoformat() if report.created_at else "",
    )


@router.post("/generate", response_model=ReportDetailResponse)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ReportDetailResponse:
    """Generate an analysis report for a document.

    Creates a formatted report from the analysis results.
    """
    document_id = UUID(request.document_id)

    # Get document
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

    # Get latest completed analysis
    analysis_result = await db.execute(
        select(AnalysisResult)
        .where(
            AnalysisResult.document_id == document_id,
            AnalysisResult.status == AnalysisStatus.COMPLETED,
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis = analysis_result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed analysis found. Run analysis first.",
        )

    # Get risk findings
    risks_result = await db.execute(
        select(AnalysisRisk)
        .where(AnalysisRisk.analysis_id == analysis.id)
        .order_by(AnalysisRisk.confidence.desc())
    )
    risks = list(risks_result.scalars().all())

    # Build report data
    import json

    # Calculate risk level
    if analysis.high_risk_count > 0:
        risk_level = "high"
    elif analysis.medium_risk_count > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Build sections
    sections = [
        {"title": "Executive Summary", "content": analysis.summary or "No summary available.", "section_type": "text"},
    ]

    # Risk assessment section
    if risks:
        risk_content = "## Risk Findings\n\n"
        for risk in risks[:20]:  # Limit to top 20
            risk_content += f"- **{risk.title}** ({risk.severity})\n"
            risk_content += f"  {risk.description or ''}\n"
            if risk.recommendation:
                risk_content += f"  *Recommendation:* {risk.recommendation}\n"
            risk_content += "\n"
        sections.append({"title": "Risk Assessment", "content": risk_content, "section_type": "list"})

    # Recommendations section
    recommendations = json.loads(analysis.recommendations) if analysis.recommendations else []
    if recommendations:
        rec_content = "## Recommendations\n\n"
        for i, rec in enumerate(recommendations, 1):
            rec_content += f"{i}. {rec}\n"
        sections.append({"title": "Recommendations", "content": rec_content, "section_type": "list"})

    risk_summary_data = {
        "total_risks": len(risks),
        "critical_count": analysis.high_risk_count,
        "high_count": analysis.high_risk_count,
        "medium_count": analysis.medium_risk_count,
        "low_count": analysis.low_risk_count,
        "overall_risk_score": analysis.overall_risk_score,
        "risk_level": risk_level,
    }

    # Create report record
    report = Report(
        document_id=document_id,
        organization_id=document.organization_id,
        analysis_id=analysis.id,
        report_type=request.report_type,
        status=ReportStatus.COMPLETED,
        title=f"Legal Analysis Report - {document.original_filename}",
        executive_summary=analysis.summary or "",
        sections=json.dumps(sections),
        risk_summary=json.dumps(risk_summary_data),
        recommendations=json.dumps(recommendations),
        overall_risk_score=analysis.overall_risk_score,
        risk_level=risk_level,
        processing_time_ms=analysis.processing_time_ms,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return _build_report_detail(report)


@router.get("/{document_id}", response_model=ReportListResponse)
async def list_reports(
    document_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> ReportListResponse:
    """List all reports for a document."""
    doc_uuid = UUID(document_id)

    result = await db.execute(
        select(Report)
        .where(Report.document_id == doc_uuid)
        .order_by(Report.created_at.desc())
    )
    reports = list(result.scalars().all())

    return ReportListResponse(
        document_id=document_id,
        reports=[_build_report_detail(r) for r in reports],
        total_count=len(reports),
    )


@router.get("/detail/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ReportDetailResponse:
    """Get a specific report by ID."""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return _build_report_detail(report)


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    request: ReportExportRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ReportExportResponse:
    """Export report in specified format.

    Formats: json, html, markdown
    """
    report_id = UUID(request.report_id)

    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Build report dict for export
    report_data = {
        "report_id": str(report.id),
        "document_id": str(report.document_id),
        "report_type": report.report_type,
        "title": report.title,
        "executive_summary": report.executive_summary or "",
        "sections": json.loads(report.sections) if report.sections else [],
        "risk_summary": json.loads(report.risk_summary) if report.risk_summary else None,
        "recommendations": json.loads(report.recommendations) if report.recommendations else [],
        "generated_at": report.created_at.isoformat() if report.created_at else "",
    }

    if request.format == "json":
        content = json.dumps(report_data, indent=2, default=str)
    elif request.format == "markdown":
        md = f"# {report.title}\n\n"
        md += f"**Generated:** {report.created_at}\n\n"
        for section in report_data.get("sections", []):
            md += f"## {section.get('title', '')}\n\n{section.get('content', '')}\n\n"
        content = md
    elif request.format == "html":
        html = f"<html><head><title>{report.title}</title></head><body>"
        html += f"<h1>{report.title}</h1>"
        for section in report_data.get("sections", []):
            html += f"<h2>{section.get('title', '')}</h2><p>{section.get('content', '')}</p>"
        html += "</body></html>"
        content = html
    elif request.format == "pdf":
        # Generate PDF using report generator
        from legallens_docproc.report_generator import (
            report_to_pdf,
        )
        from legallens_docproc.report_models import (
            AnalysisReport,
            DocumentInfo,
            ReportFormat,
            ReportType,
        )

        # Build AnalysisReport object
        pdf_report = AnalysisReport(
            report_id=str(report.id),
            document_info=DocumentInfo(
                document_id=str(report.document_id),
                filename=report.title,
                file_type="pdf",
            ),
            report_type=ReportType.FULL_ANALYSIS,
            report_format=ReportFormat.PDF,
            title=report.title,
        )
        pdf_report.executive_summary = report.executive_summary or ""
        pdf_report.sections = [
            type("Section", (), {"title": s.get("title", ""), "content": s.get("content", "")})()
            for s in report_data.get("sections", [])
        ]

        pdf_bytes = report_to_pdf(pdf_report)
        # For PDF, return base64 encoded content
        import base64

        content = base64.b64encode(pdf_bytes).decode("utf-8")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {request.format}",
        )

    return ReportExportResponse(
        report_id=str(report.id),
        format=request.format,
        content=content,
        file_size_bytes=len(content.encode()),
    )


@router.delete("/{report_id}", response_model=ReportDeleteResponse)
async def delete_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ReportDeleteResponse:
    """Delete a report."""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    await db.delete(report)

    return ReportDeleteResponse(
        report_id=str(report_id),
        deleted=True,
        message="Report deleted successfully",
    )


@router.get("/stats/overview", response_model=ReportStatsResponse)
async def get_report_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> ReportStatsResponse:
    """Get report statistics."""
    total_result = await db.execute(select(func.count(Report.id)))
    total_reports = total_result.scalar() or 0

    # Reports by type
    type_result = await db.execute(
        select(Report.report_type, func.count(Report.id)).group_by(Report.report_type)
    )
    reports_by_type = {row[0]: row[1] for row in type_result.all()}

    return ReportStatsResponse(
        total_reports=total_reports,
        reports_by_type=reports_by_type,
        reports_by_format={"json": total_reports},
        last_generated="",
    )
