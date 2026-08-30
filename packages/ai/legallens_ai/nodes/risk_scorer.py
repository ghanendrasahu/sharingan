"""Deterministic risk scorer node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)

# Configurable weights for risk dimensions
DEFAULT_WEIGHTS = {
    "legal_severity": 0.25,
    "enforceability": 0.20,
    "financial_exposure": 0.25,
    "business_impact": 0.20,
    "compliance_gap": 0.10,
}

# Score bands
SCORE_BANDS = {
    "low": (0, 29),
    "moderate": (30, 49),
    "high": (50, 69),
    "critical": (70, 100),
}


def calculate_risk_score(state: AnalysisState) -> dict[str, Any]:
    """Calculate deterministic risk score.

    This is NOT LLM-based. It uses configurable weights and
    deterministic rules to produce an explainable risk score.
    """
    risk_findings = state.get("risk_findings", [])
    missing_clauses = state.get("missing_clauses", [])
    verified_citations = state.get("verified_citations", [])

    # Calculate dimension scores
    dimensions = {}

    # Legal severity: based on risk findings
    dimensions["legal_severity"] = _calculate_legal_severity(risk_findings)

    # Enforceability: based on citation verification
    dimensions["enforceability"] = _calculate_enforceability(verified_citations)

    # Financial exposure: based on liability-related risks
    dimensions["financial_exposure"] = _calculate_financial_exposure(risk_findings)

    # Business impact: based on missing clauses and restrictions
    dimensions["business_impact"] = _calculate_business_impact(
        risk_findings, missing_clauses
    )

    # Compliance gap: based on missing critical clauses
    dimensions["compliance_gap"] = _calculate_compliance_gap(missing_clauses)

    # Calculate weighted score
    total_score = sum(
        dimensions[dim] * DEFAULT_WEIGHTS.get(dim, 0.1)
        for dim in dimensions
    )

    # Clamp to 0-100
    final_score = max(0, min(100, total_score))

    # Determine band
    risk_band = "low"
    for band, (low, high) in SCORE_BANDS.items():
        if low <= final_score <= high:
            risk_band = band
            break

    return {
        "risk_score_dimensions": dimensions,
        "final_risk_score": final_score,
        "risk_band": risk_band,
    }


def _calculate_legal_severity(risk_findings: list) -> float:
    """Calculate legal severity dimension."""
    if not risk_findings:
        return 0.0

    severity_scores = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25,
    }

    total = 0.0
    for risk in risk_findings:
        severity = getattr(risk, "severity", "medium")
        if hasattr(severity, "value"):
            severity = severity.value
        total += severity_scores.get(str(severity), 50)

    # Average, weighted by count (more risks = higher score)
    avg = total / len(risk_findings)
    count_factor = min(len(risk_findings) / 10, 1.0)  # Max out at 10 risks
    return avg * (0.5 + 0.5 * count_factor)


def _calculate_enforceability(verified_citations: list) -> float:
    """Calculate enforceability dimension based on citation verification."""
    if not verified_citations:
        return 50.0  # Unknown if no citations

    supported = sum(1 for c in verified_citations if getattr(c, "supports_claim", True))
    total = len(verified_citations)

    if total == 0:
        return 50.0

    # Higher score = better enforceability
    support_ratio = supported / total
    # Invert: poor enforceability = higher risk score
    return (1 - support_ratio) * 100


def _calculate_financial_exposure(risk_findings: list) -> float:
    """Calculate financial exposure dimension."""
    financial_keywords = [
        "liability", "penalty", "damages", "indemnif",
        "compensation", "fine", "forfeit", "penalty",
    ]

    financial_risks = 0
    for risk in risk_findings:
        title = getattr(risk, "title", "").lower()
        desc = getattr(risk, "description", "").lower()
        if any(kw in title or kw in desc for kw in financial_keywords):
            financial_risks += 1

    if not risk_findings:
        return 0.0

    return min((financial_risks / len(risk_findings)) * 100, 100)


def _calculate_business_impact(
    risk_findings: list,
    missing_clauses: list,
) -> float:
    """Calculate business impact dimension."""
    # Restriction-related risks
    restriction_keywords = ["non-compete", "restrict", "prohibit", "assign", "solicit"]
    restriction_risks = 0
    for risk in risk_findings:
        title = getattr(risk, "title", "").lower()
        if any(kw in title for kw in restriction_keywords):
            restriction_risks += 1

    # Missing critical clauses
    critical_missing = sum(
        1 for c in missing_clauses
        if getattr(c, "importance", "") == "critical"
    )

    score = 0.0
    if risk_findings:
        score += (restriction_risks / len(risk_findings)) * 50
    score += min(critical_missing * 10, 50)

    return min(score, 100)


def _calculate_compliance_gap(missing_clauses: list) -> float:
    """Calculate compliance gap dimension."""
    if not missing_clauses:
        return 0.0

    importance_weights = {
        "critical": 3,
        "important": 2,
        "recommended": 1,
    }

    total_weight = sum(
        importance_weights.get(getattr(c, "importance", "recommended"), 1)
        for c in missing_clauses
    )

    # Normalize to 0-100
    return min(total_weight * 5, 100)
