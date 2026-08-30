"""Risk analyzer node."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState, RiskFinding

logger = logging.getLogger(__name__)


def analyze_risks(state: AnalysisState) -> dict[str, Any]:
    """Analyze document clauses for legal risks.

    Node that identifies risks in each clause using LLM analysis.
    """
    from legallens_ai.state import RiskLevel

    clauses = state.get("clauses", [])
    document_text = state.get("document_text", "")

    if not clauses:
        clauses = [
            {"text": document_text[:8000], "clause_id": "full_document", "clause_type": "other"}
        ]

    all_risks: list[RiskFinding] = []

    for clause_data in clauses[:20]:
        clause_text = clause_data.get("text", "")
        clause_id = clause_data.get("clause_id", "unknown")

        if not clause_text or len(clause_text) < 20:
            continue

        risks = _analyze_clause_risks(clause_text, clause_id, document_text[:2000])
        all_risks.extend(risks)

    if all_risks:
        severity_weights = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0,
        }
        total = sum(severity_weights.get(r.severity, 0.5) for r in all_risks)
        avg_score = total / len(all_risks) if all_risks else 0
        overall_score = min(avg_score * 100, 100)
    else:
        overall_score = 0.0

    return {
        "risk_findings": all_risks,
        "overall_risk_score": overall_score,
    }


def _analyze_clause_risks(
    clause_text: str,
    clause_id: str,
    document_context: str,
) -> list[RiskFinding]:
    """Analyze risks in a single clause."""
    llm_risks = _llm_risk_analysis(clause_text, document_context)
    if llm_risks:
        return llm_risks
    return _rule_based_risk_analysis(clause_text, clause_id)


def _llm_risk_analysis(clause_text: str, document_context: str) -> list[RiskFinding]:
    """Use LLM for risk analysis."""
    from legallens_ai.nodes.classifier import _call_llm, _parse_json
    from legallens_ai.prompts import RISK_ANALYSIS_PROMPT
    from legallens_ai.state import RiskFinding, RiskLevel

    prompt = RISK_ANALYSIS_PROMPT.format(
        document_context=document_context,
        clause_text=clause_text[:3000],
    )

    try:
        response = _call_llm(prompt)
        if response:
            result = _parse_json(response)
            risks = []
            for risk_data in result.get("risks", []):
                try:
                    severity = RiskLevel(risk_data.get("severity", "medium"))
                except ValueError:
                    severity = RiskLevel.MEDIUM

                risks.append(
                    RiskFinding(
                        risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                        title=risk_data.get("title", "Unnamed risk"),
                        description=risk_data.get("description", ""),
                        severity=severity,
                        recommendation=risk_data.get("recommendation", ""),
                        confidence=risk_data.get("confidence", 0.5),
                        legal_source=risk_data.get("legal_source"),
                    )
                )
            return risks
    except Exception:
        logger.exception("LLM risk analysis failed")

    return []


def _rule_based_risk_analysis(clause_text: str, clause_id: str) -> list[RiskFinding]:
    """Rule-based risk analysis fallback."""
    from legallens_ai.state import RiskFinding, RiskLevel

    risks = []
    text_lower = clause_text.lower()

    critical_patterns = [
        (r"personal guarantee", "Personal guarantee required", "Personal assets at risk"),
        (r"unlimited liability", "Unlimited liability clause", "No cap on potential damages"),
        (r"joint and several", "Joint and several liability", "Full liability for all parties"),
        (r"all assets", "All assets at risk", "Comprehensive asset exposure"),
    ]

    for pattern, title, description in critical_patterns:
        if pattern in text_lower:
            risks.append(
                RiskFinding(
                    risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                    title=title,
                    description=description,
                    severity=RiskLevel.CRITICAL,
                    confidence=0.8,
                )
            )

    high_patterns = [
        (r"indemnif", "Indemnification clause", "May require compensating for losses"),
        (r"hold harmless", "Hold harmless clause", "May waive right to claim damages"),
        (r"penalty", "Penalty clause", "Financial penalties may apply"),
        (r"breach.*terminat", "Termination for breach", "Contract may be terminated for breach"),
        (r"irrevocable", "Irrevocable commitment", "Cannot be withdrawn once agreed"),
        (r"exclusive jurisdiction", "Exclusive jurisdiction", "Limited legal recourse options"),
    ]

    for pattern, title, description in high_patterns:
        if pattern in text_lower:
            risks.append(
                RiskFinding(
                    risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                    title=title,
                    description=description,
                    severity=RiskLevel.HIGH,
                    confidence=0.7,
                )
            )

    medium_patterns = [
        (r"shall not.*assign", "Non-assignment clause", "Rights cannot be transferred"),
        (r"non-compete", "Non-compete clause", "May restrict future business activities"),
        (r"non-solicitation", "Non-solicitation clause", "May restrict hiring former employees"),
        (r"governing law.*india", "Indian governing law", "Subject to Indian jurisdiction"),
    ]

    for pattern, title, description in medium_patterns:
        if pattern in text_lower:
            risks.append(
                RiskFinding(
                    risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                    title=title,
                    description=description,
                    severity=RiskLevel.MEDIUM,
                    confidence=0.6,
                )
            )

    return risks
