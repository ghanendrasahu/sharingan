"""Recommendation generator node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)


def generate_recommendations(state: AnalysisState) -> dict[str, Any]:
    """Generate actionable recommendations.

    Node that produces practical recommendations based on the analysis.
    """
    document_category = state.get("document_category", "unknown")
    risk_findings = state.get("risk_findings", [])
    missing_clauses = state.get("missing_clauses", [])
    risk_band = state.get("risk_band", "low")
    final_risk_score = state.get("final_risk_score", 0.0)

    # Try LLM recommendations first
    llm_recs = _llm_recommendations(
        document_category, risk_findings, missing_clauses, final_risk_score, risk_band
    )
    if llm_recs:
        return {"recommendations": llm_recs}

    # Fallback: rule-based recommendations
    return {
        "recommendations": _rule_based_recommendations(
            document_category, risk_findings, missing_clauses, risk_band
        )
    }


def _llm_recommendations(
    document_category: str,
    risk_findings: list,
    missing_clauses: list,
    risk_score: float,
    risk_band: str,
) -> list[str]:
    """Use LLM for recommendation generation."""
    from legallens_ai.nodes.classifier import _call_llm, _parse_json
    from legallens_ai.prompts import RECOMMENDATION_PROMPT

    risks_summary = (
        "\n".join(
            f"- [{getattr(r, 'severity', 'medium')}] {getattr(r, 'title', 'Unknown')}"
            for r in risk_findings[:10]
        )
        if risk_findings
        else "No risks identified"
    )

    missing_summary = (
        "\n".join(
            f"- [{getattr(c, 'importance', 'recommended')}] {getattr(c, 'clause_name', 'Unknown')}"
            for c in missing_clauses[:10]
        )
        if missing_clauses
        else "No missing clauses identified"
    )

    prompt = RECOMMENDATION_PROMPT.format(
        document_type=document_category,
        risk_score=risk_score,
        risk_band=risk_band,
        risks_summary=risks_summary,
        missing_clauses_summary=missing_summary,
    )

    try:
        response = _call_llm(prompt)
        if response:
            result = _parse_json(response)
            recs = result.get("recommendations", [])
            if recs:
                return recs
    except Exception:
        logger.exception("LLM recommendation generation failed")

    return []


def _rule_based_recommendations(
    document_category: str,
    risk_findings: list,
    missing_clauses: list,
    risk_band: str,
) -> list[str]:
    """Generate rule-based recommendations."""
    recommendations = []

    # Critical risk recommendations
    critical_risks = [
        r for r in risk_findings if str(getattr(r, "severity", "")).lower() in ("critical", "high")
    ]
    if critical_risks:
        recommendations.append(
            f"URGENT: Address {len(critical_risks)} high/critical risk items immediately. "
            "Consider legal counsel review before signing."
        )

    # Missing clause recommendations
    critical_missing = [c for c in missing_clauses if getattr(c, "importance", "") == "critical"]
    if critical_missing:
        recommendations.append(
            f"Add {len(critical_missing)} critical missing clauses: "
            + ", ".join(getattr(c, "clause_name", "Unknown") for c in critical_missing[:3])
        )

    # Document-type specific recommendations
    type_recommendations = {
        "nda": [
            "Ensure mutual obligations are clearly defined",
            "Define what constitutes confidential information",
            "Include exceptions for publicly available information",
        ],
        "employment": [
            "Ensure compliance with Industrial Disputes Act for termination",
            "Clearly define intellectual property assignment",
            "Include non-compete only if reasonable in scope and duration",
        ],
        "lease": [
            "Document the condition of premises at time of lease",
            "Clearly define maintenance responsibilities",
            "Include rent escalation clause if applicable",
        ],
        "vendor": [
            "Define service level agreements with measurable metrics",
            "Include liability caps and limitation of liability clause",
            "Ensure intellectual property ownership is clear",
        ],
        "consultancy": [
            "Clarify independent contractor status to avoid employment misclassification",
            "Define deliverables and timeline clearly",
            "Include TDS compliance provisions",
        ],
        "founder": [
            "Include vesting schedule with cliff period",
            "Define decision-making authority clearly",
            "Include exit provisions and buyout mechanisms",
        ],
        "term_sheet": [
            "Ensure anti-dilution provisions are balanced",
            "Define liquidation preference clearly",
            "Include drag-along and tag-along rights",
        ],
    }

    doc_recs = type_recommendations.get(document_category, [])
    recommendations.extend(doc_recs[:3])

    # Risk band recommendations
    if risk_band == "critical":
        recommendations.insert(
            0, "WARNING: This document has critical risk level. Do not sign without legal review."
        )
    elif risk_band == "high":
        recommendations.insert(
            0, "This document has high risk level. Strongly recommend legal review."
        )

    # General best practices
    recommendations.append("Ensure all parties have signed the final version")
    recommendations.append("Keep a signed copy for your records")

    return recommendations[:10]  # Limit to 10 recommendations
