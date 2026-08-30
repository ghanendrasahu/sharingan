"""Quality checker node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)


def check_quality(state: AnalysisState) -> dict[str, Any]:
    """Perform quality checks on the analysis results.

    Node that validates the analysis output quality.
    """
    checks = []

    # Check 1: Document was classified
    checks.append(_check_classification(state))

    # Check 2: Risks were identified (or document is clean)
    checks.append(_check_risk_analysis(state))

    # Check 3: Missing clauses were checked
    checks.append(_check_missing_clauses(state))

    # Check 4: Evidence was verified
    checks.append(_check_evidence(state))

    # Check 5: Risk score is reasonable
    checks.append(_check_risk_score(state))

    # Check 6: Recommendations exist
    checks.append(_check_recommendations(state))

    # Overall quality
    passed = all(c.passed for c in checks if c.check_name != "risk_analysis")

    return {
        "quality_checks": checks,
        "quality_passed": passed,
    }


def _check_classification(state: AnalysisState) -> Any:
    """Check that document was classified."""
    from legallens_ai.state import QualityCheck

    category = state.get("document_category", "unknown")
    confidence = state.get("classification_confidence", 0.0)

    if category == "unknown":
        return QualityCheck(
            check_name="classification",
            passed=False,
            message="Document could not be classified",
            score=0.0,
        )

    if confidence < 0.3:
        return QualityCheck(
            check_name="classification",
            passed=True,
            message=f"Classified as {category} with low confidence ({confidence:.0%})",
            score=confidence,
        )

    return QualityCheck(
        check_name="classification",
        passed=True,
        message=f"Classified as {category} with confidence {confidence:.0%}",
        score=confidence,
    )


def _check_risk_analysis(state: AnalysisState) -> Any:
    """Check that risk analysis was performed."""
    from legallens_ai.state import QualityCheck

    risk_findings = state.get("risk_findings", [])
    document_text = state.get("document_text", "")

    if not document_text:
        return QualityCheck(
            check_name="risk_analysis",
            passed=False,
            message="No document text provided",
            score=0.0,
        )

    # It's OK if no risks found - document might be clean
    return QualityCheck(
        check_name="risk_analysis",
        passed=True,
        message=f"Analyzed {len(risk_findings)} risks",
        score=1.0 if risk_findings else 0.8,
    )


def _check_missing_clauses(state: AnalysisState) -> Any:
    """Check that missing clause analysis was performed."""
    from legallens_ai.state import QualityCheck

    missing = state.get("missing_clauses", [])

    return QualityCheck(
        check_name="missing_clauses",
        passed=True,
        message=f"Identified {len(missing)} potential missing clauses",
        score=1.0,
    )


def _check_evidence(state: AnalysisState) -> Any:
    """Check that evidence was verified."""
    from legallens_ai.state import QualityCheck

    citations = state.get("verified_citations", [])

    if not citations:
        return QualityCheck(
            check_name="evidence",
            passed=True,
            message="No citations to verify",
            score=0.8,
        )

    supported = sum(1 for c in citations if getattr(c, "supports_claim", True))
    total = len(citations)
    score = supported / total if total > 0 else 0.5

    return QualityCheck(
        check_name="evidence",
        passed=score >= 0.3,
        message=f"Verified {supported}/{total} citations ({score:.0%} supported)",
        score=score,
    )


def _check_risk_score(state: AnalysisState) -> Any:
    """Check that risk score is reasonable."""
    from legallens_ai.state import QualityCheck

    score = state.get("final_risk_score", 0.0)
    risk_band = state.get("risk_band", "low")

    if score < 0 or score > 100:
        return QualityCheck(
            check_name="risk_score",
            passed=False,
            message=f"Invalid risk score: {score}",
            score=0.0,
        )

    return QualityCheck(
        check_name="risk_score",
        passed=True,
        message=f"Risk score: {score:.1f}/100 ({risk_band})",
        score=1.0,
    )


def _check_recommendations(state: AnalysisState) -> Any:
    """Check that recommendations were generated."""
    from legallens_ai.state import QualityCheck

    recommendations = state.get("recommendations", [])

    if not recommendations:
        return QualityCheck(
            check_name="recommendations",
            passed=False,
            message="No recommendations generated",
            score=0.0,
        )

    return QualityCheck(
        check_name="recommendations",
        passed=True,
        message=f"Generated {len(recommendations)} recommendations",
        score=1.0,
    )
