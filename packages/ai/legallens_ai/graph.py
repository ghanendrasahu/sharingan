"""LangGraph analysis graph."""

from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import END, StateGraph

from legallens_ai.nodes import (
    analyze_risks,
    calculate_risk_score,
    check_quality,
    classify_document,
    detect_missing_clauses,
    generate_recommendations,
    retrieve_legal_sources,
    verify_evidence,
)
from legallens_ai.state import AnalysisState, create_initial_state

logger = logging.getLogger(__name__)


def _route_after_classification(state: AnalysisState) -> str:
    """Route after classification based on confidence."""
    confidence = state.get("classification_confidence", 0.0)
    if confidence < 0.3:
        return "risk_analysis"  # Proceed even with low confidence
    return "risk_analysis"


def _route_after_quality(state: AnalysisState) -> str:
    """Route after quality check."""
    # Always end after quality check
    return END


def build_analysis_graph() -> StateGraph:
    """Build the legal document analysis graph.

    Pipeline:
    1. Classify document
    2. Analyze risks
    3. Detect missing clauses
    4. Retrieve legal sources
    5. Verify evidence
    6. Calculate risk score
    7. Generate recommendations
    8. Quality check
    """
    graph = StateGraph(AnalysisState)

    # Add nodes
    graph.add_node("classify", classify_document)
    graph.add_node("risk_analysis", analyze_risks)
    graph.add_node("missing_clauses", detect_missing_clauses)
    graph.add_node("legal_retrieval", retrieve_legal_sources)
    graph.add_node("evidence_verification", verify_evidence)
    graph.add_node("risk_scoring", calculate_risk_score)
    graph.add_node("recommendations", generate_recommendations)
    graph.add_node("quality_check", check_quality)

    # Set entry point
    graph.set_entry_point("classify")

    # Add edges
    graph.add_conditional_edges(
        "classify",
        _route_after_classification,
        {"risk_analysis": "risk_analysis"},
    )
    graph.add_edge("risk_analysis", "missing_clauses")
    graph.add_edge("missing_clauses", "legal_retrieval")
    graph.add_edge("legal_retrieval", "evidence_verification")
    graph.add_edge("evidence_verification", "risk_scoring")
    graph.add_edge("risk_scoring", "recommendations")
    graph.add_edge("recommendations", "quality_check")
    graph.add_conditional_edges(
        "quality_check",
        _route_after_quality,
        {END: END},
    )

    return graph.compile()


def run_analysis(
    document_id: str,
    document_text: str,
    clauses: list[dict] | None = None,
    document_type_hint: str | None = None,
) -> dict[str, Any]:
    """Run the full analysis pipeline.

    This is the main entry point for running analysis.
    """
    start_time = time.time()

    # Create initial state
    state = create_initial_state(
        document_id=document_id,
        document_text=document_text,
        clauses=clauses,
        document_type_hint=document_type_hint,
    )

    try:
        # Build and run graph
        graph = build_analysis_graph()
        result = graph.invoke(state)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Extract results
        return {
            "success": True,
            "document_id": document_id,
            "document_category": result.get("document_category", "unknown"),
            "classification_confidence": result.get("classification_confidence", 0.0),
            "risk_findings": result.get("risk_findings", []),
            "overall_risk_score": result.get("overall_risk_score", 0.0),
            "missing_clauses": result.get("missing_clauses", []),
            "verified_citations": result.get("verified_citations", []),
            "risk_score_dimensions": result.get("risk_score_dimensions", {}),
            "final_risk_score": result.get("final_risk_score", 0.0),
            "risk_band": result.get("risk_band", "low"),
            "recommendations": result.get("recommendations", []),
            "quality_checks": result.get("quality_checks", []),
            "quality_passed": result.get("quality_passed", False),
            "executive_summary": result.get("executive_summary", ""),
            "processing_time_ms": processing_time,
            "error": result.get("error"),
        }

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.exception("Analysis pipeline failed")
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e),
            "processing_time_ms": processing_time,
        }
