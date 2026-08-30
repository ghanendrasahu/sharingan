"""Report generation service for legal document analysis."""

from __future__ import annotations

import json
import time
import uuid
from typing import TYPE_CHECKING

from legallens_docproc.analysis_models import AIAnalysisResult, RiskSeverity
from legallens_docproc.report_models import (
    AnalysisReport,
    DocumentInfo,
    ReportFormat,
    ReportSection,
    ReportType,
    RiskSummary,
)

if TYPE_CHECKING:
    from legallens_docproc.clause_models import Clause


class ReportGenerationError(Exception):
    """Error during report generation."""

    def __init__(self, message: str, code: str = "REPORT_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


def _calculate_risk_summary(analysis_result: AIAnalysisResult) -> RiskSummary:
    """Calculate risk summary from analysis result."""
    total_risks = len(analysis_result.risk_findings)
    critical_count = sum(
        1 for r in analysis_result.risk_findings if r.severity == RiskSeverity.CRITICAL
    )
    high_count = sum(1 for r in analysis_result.risk_findings if r.severity == RiskSeverity.HIGH)
    medium_count = sum(
        1 for r in analysis_result.risk_findings if r.severity == RiskSeverity.MEDIUM
    )
    low_count = sum(1 for r in analysis_result.risk_findings if r.severity == RiskSeverity.LOW)

    # Determine overall risk level
    if critical_count > 0:
        risk_level = "critical"
    elif high_count > 0:
        risk_level = "high"
    elif medium_count > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskSummary(
        total_risks=total_risks,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        overall_risk_score=analysis_result.overall_risk_score,
        risk_level=risk_level,
    )


def _create_executive_summary_section(analysis_result: AIAnalysisResult) -> ReportSection:
    """Create executive summary section."""
    content = analysis_result.summary or "No summary available."

    # Add key metrics
    content += f"\n\n**Risk Score:** {analysis_result.overall_risk_score:.1%}"
    content += f"\n**Total Risks Identified:** {len(analysis_result.risk_findings)}"
    content += f"\n**Key Terms Found:** {len(analysis_result.key_terms)}"

    return ReportSection(
        title="Executive Summary",
        content=content,
        section_type="text",
    )


def _create_risk_assessment_section(analysis_result: AIAnalysisResult) -> ReportSection:
    """Create risk assessment section."""
    if not analysis_result.risk_findings:
        return ReportSection(
            title="Risk Assessment",
            content="No risks identified in the document.",
            section_type="text",
        )

    content = "## Risk Findings\n\n"

    # Group by severity
    for severity in [
        RiskSeverity.CRITICAL,
        RiskSeverity.HIGH,
        RiskSeverity.MEDIUM,
        RiskSeverity.LOW,
    ]:
        findings = [r for r in analysis_result.risk_findings if r.severity == severity]
        if findings:
            content += f"### {severity.value.upper()} Risk\n\n"
            for finding in findings:
                content += f"- **{finding.title}**\n"
                content += f"  {finding.description}\n"
                if finding.recommendation:
                    content += f"  *Recommendation:* {finding.recommendation}\n"
                content += "\n"

    return ReportSection(
        title="Risk Assessment",
        content=content,
        section_type="list",
        data={
            "critical": analysis_result.high_risk_count,
            "medium": analysis_result.medium_risk_count,
            "low": analysis_result.low_risk_count,
        },
    )


def _create_key_terms_section(analysis_result: AIAnalysisResult) -> ReportSection:
    """Create key terms section."""
    if not analysis_result.key_terms:
        return ReportSection(
            title="Key Terms",
            content="No key terms identified.",
            section_type="text",
        )

    content = "## Key Terms and Definitions\n\n"
    for term in analysis_result.key_terms:
        content += f"- **{term.term}**"
        if term.definition:
            content += f": {term.definition}"
        if term.section_reference:
            content += f" (Ref: {term.section_reference})"
        content += "\n"

    return ReportSection(
        title="Key Terms",
        content=content,
        section_type="list",
        data=[{"term": t.term, "definition": t.definition} for t in analysis_result.key_terms],
    )


def _create_recommendations_section(analysis_result: AIAnalysisResult) -> ReportSection:
    """Create recommendations section."""
    if not analysis_result.recommendations:
        return ReportSection(
            title="Recommendations",
            content="No specific recommendations.",
            section_type="text",
        )

    content = "## Recommendations\n\n"
    for i, rec in enumerate(analysis_result.recommendations, 1):
        content += f"{i}. {rec}\n"

    return ReportSection(
        title="Recommendations",
        content=content,
        section_type="list",
        data=analysis_result.recommendations,
    )


def generate_analysis_report(
    document_id: str,
    filename: str,
    file_type: str,
    analysis_result: AIAnalysisResult,
    clauses: list[Clause] | None = None,
    report_type: ReportType = ReportType.FULL_ANALYSIS,
    report_format: ReportFormat = ReportFormat.JSON,
) -> AnalysisReport:
    """Generate a complete analysis report."""
    start_time = time.time()

    # Create document info
    doc_info = DocumentInfo(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        total_clauses=len(clauses) if clauses else 0,
    )

    # Create report
    report = AnalysisReport(
        report_id=f"report_{uuid.uuid4().hex[:8]}",
        document_info=doc_info,
        report_type=report_type,
        report_format=report_format,
        title=f"Legal Analysis Report - {filename}",
    )

    try:
        # Calculate risk summary
        report.risk_summary = _calculate_risk_summary(analysis_result)

        # Add sections
        report.add_section(
            "Executive Summary",
            _create_executive_summary_section(analysis_result).content,
        )

        if report_type in [ReportType.RISK_ASSESSMENT, ReportType.FULL_ANALYSIS]:
            report.add_section(
                "Risk Assessment",
                _create_risk_assessment_section(analysis_result).content,
            )

        if report_type in [ReportType.FULL_ANALYSIS, ReportType.CLAUSE_ANALYSIS]:
            report.add_section(
                "Key Terms",
                _create_key_terms_section(analysis_result).content,
            )

        report.add_section(
            "Recommendations",
            _create_recommendations_section(analysis_result).content,
        )

        # Add key terms and recommendations
        report.key_terms = [
            {"term": t.term, "definition": t.definition} for t in analysis_result.key_terms
        ]
        report.recommendations = analysis_result.recommendations

    except Exception as e:
        report.error = f"Report generation failed: {e!s}"

    report.processing_time_ms = (time.time() - start_time) * 1000
    return report


def report_to_json(report: AnalysisReport) -> str:
    """Convert report to JSON string."""
    return json.dumps(report.to_dict(), indent=2, default=str)


def report_to_markdown(report: AnalysisReport) -> str:
    """Convert report to Markdown format."""
    md = f"# {report.title}\n\n"
    md += f"**Report ID:** {report.report_id}\n"
    md += f"**Generated:** {report.generated_at}\n"
    md += f"**Document:** {report.document_info.filename}\n\n"

    md += "---\n\n"

    md += f"## {report.executive_summary}\n\n"

    for section in report.sections:
        md += f"## {section.title}\n\n"
        md += f"{section.content}\n\n"

    return md


def report_to_html(report: AnalysisReport) -> str:
    """Convert report to HTML format."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .risk-critical {{ color: #e74c3c; font-weight: bold; }}
        .risk-high {{ color: #e67e22; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; }}
        .risk-low {{ color: #27ae60; }}
        ul {{ margin-left: 20px; }}
        li {{ margin-bottom: 10px; }}
        .disclaimer {{ margin-top: 40px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <div class="metadata">
        <p><strong>Report ID:</strong> {report.report_id}</p>
        <p><strong>Generated:</strong> {report.generated_at}</p>
        <p><strong>Document:</strong> {report.document_info.filename}</p>
    </div>
"""

    for section in report.sections:
        html += f"    <h2>{section.title}</h2>\n"
        content = section.content.replace("\n", "<br>\n")
        html += f"    <div>{content}</div>\n\n"

    html += """
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This report is generated by AI and is for informational purposes only.
        It does not constitute legal advice. Please consult a qualified legal professional for any legal decisions.
    </div>
</body>
</html>"""

    return html


def report_to_pdf(report: AnalysisReport) -> bytes:
    """Convert report to PDF format.

    Uses weasyprint if available, falls back to HTML output.
    """
    html_content = report_to_html(report)

    try:
        from weasyprint import HTML  # type: ignore[import-untyped, reportMissingImports]

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        import logging

        logging.getLogger(__name__).warning(
            "weasyprint not installed, returning HTML as PDF fallback"
        )
        return html_content.encode("utf-8")
