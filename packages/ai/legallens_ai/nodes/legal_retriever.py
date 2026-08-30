"""Legal retriever node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)


def retrieve_legal_sources(state: AnalysisState) -> dict[str, Any]:
    """Retrieve relevant legal sources for the document analysis.

    Node that finds applicable Indian laws and regulations.
    """
    document_category = state.get("document_category", "unknown")
    risk_findings = state.get("risk_findings", [])

    # Map document categories to relevant legal sources
    legal_source_map = {
        "employment": [
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["1-238"],
                "relevance": "employment contracts",
            },
            {
                "source": "Industrial Disputes Act, 1947",
                "sections": ["25F", "25G"],
                "relevance": "termination",
            },
            {
                "source": "Payment of Wages Act, 1936",
                "sections": ["all"],
                "relevance": "salary payments",
            },
        ],
        "nda": [
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["27"],
                "relevance": "non-compete enforceability",
            },
            {
                "source": "Information Technology Act, 2000",
                "sections": ["43A"],
                "relevance": "data protection",
            },
            {
                "source": "Indian Penal Code, 1860",
                "sections": ["405-409"],
                "relevance": "criminal breach of trust",
            },
        ],
        "lease": [
            {
                "source": "Transfer of Property Act, 1882",
                "sections": ["105-117"],
                "relevance": "lease provisions",
            },
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["106"],
                "relevance": "notice to quit",
            },
            {
                "source": "Rent Control Acts",
                "sections": ["state-specific"],
                "relevance": "rent regulation",
            },
        ],
        "vendor": [
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["1-238"],
                "relevance": "contract terms",
            },
            {"source": "Sale of Goods Act, 1930", "sections": ["all"], "relevance": "goods supply"},
            {
                "source": "Goods and Services Tax Act, 2017",
                "sections": ["all"],
                "relevance": "tax obligations",
            },
        ],
        "consultancy": [
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["1-238"],
                "relevance": "service agreements",
            },
            {
                "source": "Income Tax Act, 1961",
                "sections": ["194J"],
                "relevance": "TDS on professional fees",
            },
        ],
        "founder": [
            {
                "source": "Companies Act, 2013",
                "sections": ["2-122"],
                "relevance": "company formation",
            },
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["27"],
                "relevance": "non-compete enforceability",
            },
            {"source": "SEBI Regulations", "sections": ["all"], "relevance": "equity issuance"},
        ],
        "term_sheet": [
            {
                "source": "Companies Act, 2013",
                "sections": ["62", "73"],
                "relevance": "equity issuance",
            },
            {
                "source": "SEBI (ICDR) Regulations",
                "sections": ["all"],
                "relevance": "issue of capital",
            },
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["10"],
                "relevance": "valid agreement",
            },
        ],
    }

    # Get base sources for document type
    base_sources = legal_source_map.get(
        document_category,
        [
            {
                "source": "Indian Contract Act, 1872",
                "sections": ["1-238"],
                "relevance": "general contract law",
            },
        ],
    )

    # Add risk-specific sources
    risk_sources = []
    for risk in risk_findings[:10]:
        if hasattr(risk, "legal_source") and risk.legal_source:
            risk_sources.append({"source": risk.legal_source, "relevance": risk.title})

    # Combine and deduplicate
    all_sources = base_sources + risk_sources
    seen = set()
    unique_sources = []
    for source in all_sources:
        key = source.get("source", "")
        if key not in seen:
            seen.add(key)
            unique_sources.append(source)

    return {"retrieved_legal_sources": unique_sources}
