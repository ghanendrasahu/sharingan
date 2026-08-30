"""Missing clause detection node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)

# Standard clauses expected per document type
STANDARD_CLAUSES: dict[str, list[dict[str, str]]] = {
    "nda": [
        {
            "name": "Definition of Confidential Information",
            "type": "definition",
            "importance": "critical",
        },
        {"name": "Obligations of Receiving Party", "type": "obligation", "importance": "critical"},
        {
            "name": "Exclusions from Confidential Information",
            "type": "condition",
            "importance": "important",
        },
        {"name": "Term and Termination", "type": "termination", "importance": "critical"},
        {"name": "Return of Materials", "type": "obligation", "importance": "important"},
        {"name": "Remedies for Breach", "type": "remedy", "importance": "critical"},
        {"name": "Governing Law", "type": "governing_law", "importance": "critical"},
    ],
    "employment": [
        {"name": "Job Description and Duties", "type": "obligation", "importance": "critical"},
        {"name": "Compensation and Benefits", "type": "condition", "importance": "critical"},
        {"name": "Termination Clause", "type": "termination", "importance": "critical"},
        {"name": "Non-Compete", "type": "restriction", "importance": "important"},
        {"name": "Intellectual Property Assignment", "type": "ip_rights", "importance": "critical"},
        {"name": "Confidentiality", "type": "confidentiality", "importance": "critical"},
        {"name": "Dispute Resolution", "type": "dispute_resolution", "importance": "important"},
    ],
    "lease": [
        {"name": "Premises Description", "type": "definition", "importance": "critical"},
        {"name": "Rent and Payment Terms", "type": "condition", "importance": "critical"},
        {"name": "Security Deposit", "type": "condition", "importance": "important"},
        {"name": "Maintenance Responsibilities", "type": "obligation", "importance": "important"},
        {"name": "Termination and Notice", "type": "termination", "importance": "critical"},
        {"name": "Subletting Restrictions", "type": "restriction", "importance": "important"},
        {"name": "Governing Law", "type": "governing_law", "importance": "critical"},
    ],
    "vendor": [
        {"name": "Scope of Services", "type": "definition", "importance": "critical"},
        {"name": "Payment Terms", "type": "condition", "importance": "critical"},
        {"name": "Service Level Agreement", "type": "obligation", "importance": "important"},
        {"name": "Liability Limitation", "type": "liability", "importance": "critical"},
        {"name": "Intellectual Property", "type": "ip_rights", "importance": "important"},
        {"name": "Confidentiality", "type": "confidentiality", "importance": "important"},
        {"name": "Termination", "type": "termination", "importance": "important"},
    ],
    "consultancy": [
        {"name": "Scope of Engagement", "type": "definition", "importance": "critical"},
        {"name": "Fees and Payment", "type": "condition", "importance": "critical"},
        {"name": "Independent Contractor Status", "type": "definition", "importance": "critical"},
        {"name": "IP Ownership", "type": "ip_rights", "importance": "critical"},
        {"name": "Confidentiality", "type": "confidentiality", "importance": "critical"},
        {"name": "Termination", "type": "termination", "importance": "important"},
        {"name": "Non-Solicitation", "type": "restriction", "importance": "recommended"},
    ],
    "founder": [
        {"name": "Equity Split", "type": "condition", "importance": "critical"},
        {"name": "Vesting Schedule", "type": "condition", "importance": "critical"},
        {"name": "Roles and Responsibilities", "type": "obligation", "importance": "critical"},
        {"name": "Decision Making", "type": "condition", "importance": "critical"},
        {"name": "Exit Provisions", "type": "termination", "importance": "critical"},
        {"name": "Non-Compete", "type": "restriction", "importance": "important"},
        {"name": "Intellectual Property Assignment", "type": "ip_rights", "importance": "critical"},
    ],
    "term_sheet": [
        {"name": "Valuation", "type": "condition", "importance": "critical"},
        {"name": "Investment Amount", "type": "condition", "importance": "critical"},
        {"name": "Equity Dilution", "type": "condition", "importance": "critical"},
        {"name": "Board Composition", "type": "condition", "importance": "important"},
        {"name": "Anti-Dilution", "type": "condition", "importance": "important"},
        {"name": "Liquidation Preference", "type": "condition", "importance": "critical"},
        {"name": "Drag Along Rights", "type": "right", "importance": "important"},
    ],
}


def detect_missing_clauses(state: AnalysisState) -> dict[str, Any]:
    """Detect missing clauses based on document type.

    Node that identifies important clauses that should be present but aren't.
    """
    from legallens_ai.state import MissingClause

    document_category = state.get("document_category", "unknown")
    clauses = state.get("clauses", [])
    document_text = state.get("document_text", "")

    # Get expected clauses for this document type
    expected = STANDARD_CLAUSES.get(document_category, [])
    if not expected:
        # For unknown types, check all standard clauses
        expected = []

    # Get existing clause types
    existing_types = set()
    existing_texts = []
    for clause in clauses:
        ct = clause.get("clause_type", "other")
        existing_types.add(ct)
        existing_texts.append(clause.get("text", "").lower())

    # Check for missing clauses using LLM
    llm_missing = _llm_missing_clause_analysis(document_text, document_category, clauses)
    if llm_missing:
        return {"missing_clauses": llm_missing}

    # Fallback: rule-based detection
    missing = []

    for expected_clause in expected:
        clause_name = expected_clause["name"]
        # Check if clause exists by name or similar content
        found = False
        for text in existing_texts:
            if clause_name.lower() in text or _fuzzy_match(clause_name, text):
                found = True
                break

        if not found:
            missing.append(
                MissingClause(
                    clause_name=clause_name,
                    description=f"Standard {document_category} clause that should be included",
                    importance=expected_clause["importance"],
                    clause_type=expected_clause["type"],
                    confidence=0.7,
                )
            )

    return {"missing_clauses": missing}


def _llm_missing_clause_analysis(
    document_text: str,
    document_type: str,
    clauses: list[dict],
) -> list[Any]:
    """Use LLM for missing clause analysis."""
    from legallens_ai.nodes.classifier import _call_llm, _parse_json
    from legallens_ai.prompts import MISSING_CLAUSE_PROMPT
    from legallens_ai.state import MissingClause

    existing_clauses_text = (
        "\n".join(
            f"- {c.get('clause_type', 'unknown')}: {c.get('text', '')[:100]}..."
            for c in clauses[:10]
        )
        if clauses
        else "No clauses identified"
    )

    prompt = MISSING_CLAUSE_PROMPT.format(
        document_type=document_type,
        document_text=document_text[:3000],
        existing_clauses=existing_clauses_text,
    )

    try:
        response = _call_llm(prompt)
        if response:
            result = _parse_json(response)
            missing = []
            for item in result.get("missing_clauses", []):
                missing.append(
                    MissingClause(
                        clause_name=item.get("clause_name", "Unknown clause"),
                        description=item.get("description", ""),
                        importance=item.get("importance", "recommended"),
                        clause_type=item.get("clause_type", "other"),
                        example_drafting=item.get("example_drafting", ""),
                        confidence=item.get("confidence", 0.5),
                    )
                )
            return missing
    except Exception:
        logger.exception("LLM missing clause analysis failed")

    return []


def _fuzzy_match(expected: str, text: str) -> bool:
    """Simple fuzzy matching for clause names."""
    expected_words = set(expected.lower().split())
    text_words = set(text.split())
    # If most words from expected are in text, consider it a match
    if len(expected_words) > 0:
        overlap = expected_words & text_words
        return len(overlap) / len(expected_words) > 0.6
    return False
