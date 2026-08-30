"""Evidence verifier node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)


def verify_evidence(state: AnalysisState) -> dict[str, Any]:
    """Verify legal citations and evidence.

    Node that validates that legal claims are supported by actual sources.
    """
    risk_findings = state.get("risk_findings", [])
    retrieved_sources = state.get("retrieved_legal_sources", [])

    # Collect claims that reference legal sources
    claims = []
    for risk in risk_findings[:15]:
        if hasattr(risk, "legal_source") and risk.legal_source:
            claims.append(
                {
                    "claim": f"{risk.title}: {risk.description}",
                    "source": risk.legal_source,
                }
            )

    if not claims:
        # No claims to verify
        return {"verified_citations": []}

    # Try LLM verification
    llm_citations = _llm_verify_claims(claims)
    if llm_citations:
        return {"verified_citations": llm_citations}

    # Fallback: rule-based verification
    return {"verified_citations": _rule_based_verification(claims, retrieved_sources)}


def _llm_verify_claims(claims: list[dict]) -> list[Any]:
    """Use LLM to verify legal claims."""
    from legallens_ai.nodes.classifier import _call_llm, _parse_json
    from legallens_ai.prompts import EVIDENCE_VERIFICATION_PROMPT
    from legallens_ai.state import VerifiedCitation

    claims_text = "\n".join(f"- {c['claim']} (Source: {c['source']})" for c in claims)
    prompt = EVIDENCE_VERIFICATION_PROMPT.format(claims=claims_text)

    try:
        response = _call_llm(prompt)
        if response:
            result = _parse_json(response)
            citations = []
            for item in result.get("verified_citations", []):
                citations.append(
                    VerifiedCitation(
                        citation=item.get("citation", ""),
                        source=item.get("source", ""),
                        section=item.get("section"),
                        supports_claim=item.get("supports_claim", True),
                        confidence=item.get("confidence", 0.5),
                    )
                )
            return citations
    except Exception:
        logger.exception("LLM evidence verification failed")

    return []


def _rule_based_verification(
    claims: list[dict],
    retrieved_sources: list[dict],
) -> list[Any]:
    """Rule-based verification of legal claims."""
    from legallens_ai.state import VerifiedCitation

    # Known valid Indian legal citations
    known_citations = {
        "indian contract act": {"source": "Indian Contract Act, 1872", "valid": True},
        "section 27": {
            "source": "Indian Contract Act, 1872",
            "section": "27",
            "valid": True,
            "note": "Non-compete restrictions",
        },
        "section 10": {
            "source": "Indian Contract Act, 1872",
            "section": "10",
            "valid": True,
            "note": "Valid contract requirements",
        },
        "it act": {"source": "Information Technology Act, 2000", "valid": True},
        "section 43a": {
            "source": "Information Technology Act, 2000",
            "section": "43A",
            "valid": True,
            "note": "Data protection",
        },
        "companies act": {"source": "Companies Act, 2013", "valid": True},
        "dpdp": {"source": "Digital Personal Data Protection Act, 2023", "valid": True},
        "arbitration act": {"source": "Arbitration and Conciliation Act, 1996", "valid": True},
    }

    citations = []
    for claim in claims:
        claim_text = claim.get("claim", "").lower()
        source_hint = claim.get("source", "").lower()

        # Check if source is known and valid
        verified = False
        confidence = 0.5
        citation_text = ""
        section = None

        for key, info in known_citations.items():
            if key in source_hint or key in claim_text:
                verified = info["valid"]
                citation_text = info["source"]
                section = info.get("section")
                confidence = 0.8 if verified else 0.3
                break

        citations.append(
            VerifiedCitation(
                citation=citation_text or source_hint,
                source=citation_text or "Unknown source",
                section=section,
                supports_claim=verified,
                confidence=confidence,
            )
        )

    return citations
