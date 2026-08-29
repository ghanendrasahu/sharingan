"""Clause segmentation service for legal documents."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from legallens_docproc.clause_models import (
    Clause,
    ClauseRiskLevel,
    ClauseSegmentationResult,
    ClauseType,
)

if TYPE_CHECKING:
    from legallens_docproc.models import ProcessedDocument


@dataclass
class ClausePattern:
    """Pattern for detecting clause boundaries."""

    pattern: re.Pattern
    clause_type: ClauseType
    confidence: float = 0.8


# Common clause patterns in Indian legal documents
CLAUSE_PATTERNS: list[ClausePattern] = [
    # Numbered clauses (1., 1.1, (a), (i), etc.)
    ClausePattern(
        pattern=re.compile(
            r"^(?:\d+\.(?:\d+)*\.?\s|[a-z]\.\s|\([a-z]\)\s|\([ivx]+\)\s)",
            re.MULTILINE | re.IGNORECASE,
        ),
        clause_type=ClauseType.OTHER,
        confidence=0.9,
    ),
    # Section headers
    ClausePattern(
        pattern=re.compile(
            r"^(?:SECTION|Section)\s+\d+",
            re.MULTILINE,
        ),
        clause_type=ClauseType.OTHER,
        confidence=0.95,
    ),
    # Definitions
    ClausePattern(
        pattern=re.compile(
            r"(?:'[^']+'|\"[^\"]+\"|Definitions?|means?|shall mean)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.DEFINITION,
        confidence=0.7,
    ),
    # Obligations
    ClausePattern(
        pattern=re.compile(
            r"(?:shall|must|will|agree to|obligated to|required to)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.OBLIGATION,
        confidence=0.6,
    ),
    # Rights
    ClausePattern(
        pattern=re.compile(
            r"(?:may|entitled to|right to|有权|right of)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.RIGHT,
        confidence=0.5,
    ),
    # Restrictions
    ClausePattern(
        pattern=re.compile(
            r"(?:shall not|must not|will not|prohibited|restricted|not permitted)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.RESTRICTION,
        confidence=0.7,
    ),
    # Indemnity
    ClausePattern(
        pattern=re.compile(
            r"(?:indemnif|hold harmless|defend)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.INDEMNITY,
        confidence=0.85,
    ),
    # Termination
    ClausePattern(
        pattern=re.compile(
            r"(?:terminat|expir|end|cancel|rescind|void)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.TERMINATION,
        confidence=0.7,
    ),
    # Confidentiality
    ClausePattern(
        pattern=re.compile(
            r"(?:confidential|non-disclosure|secret|proprietary)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.CONFIDENTIALITY,
        confidence=0.85,
    ),
    # IP Rights
    ClausePattern(
        pattern=re.compile(
            r"(?:intellectual property|copyright|trademark|patent|IP rights)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.IP_RIGHTS,
        confidence=0.85,
    ),
    # Liability
    ClausePattern(
        pattern=re.compile(
            r"(?:liability|liable|limitation of liability|damages)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.LIABILITY,
        confidence=0.8,
    ),
    # Dispute Resolution
    ClausePattern(
        pattern=re.compile(
            r"(?:dispute resolution|arbitration|mediation|jurisdiction)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.DISPUTE_RESOLUTION,
        confidence=0.9,
    ),
    # Governing Law
    ClausePattern(
        pattern=re.compile(
            r"(?:governing law|applicable law|laws of India|Indian law)",
            re.IGNORECASE,
        ),
        clause_type=ClauseType.GOVERNING_LAW,
        confidence=0.95,
    ),
]


def detect_clause_boundaries(text: str) -> list[int]:
    """Detect clause boundaries in text.

    Returns list of character positions where clauses start.
    """
    boundaries = []

    # Pattern for numbered clauses
    numbered_pattern = re.compile(
        r"^(?:\d+\.(?:\d+)*\.?\s|[A-Z]\.\s|[a-z]\.\s|\([a-z]\)\s)",
        re.MULTILINE,
    )

    for match in numbered_pattern.finditer(text):
        boundaries.append(match.start())

    # Always include start
    if not boundaries or boundaries[0] != 0:
        boundaries.insert(0, 0)

    return sorted(set(boundaries))


def classify_clause(text: str) -> tuple[ClauseType, float]:
    """Classify a clause based on its content.

    Returns (clause_type, confidence).
    """
    best_type = ClauseType.OTHER
    best_confidence = 0.0

    for clause_pattern in CLAUSE_PATTERNS:
        matches = clause_pattern.pattern.findall(text)
        if matches:
            # Confidence increases with more matches
            match_confidence = min(
                clause_pattern.confidence + (len(matches) - 1) * 0.05,
                1.0,
            )
            if match_confidence > best_confidence:
                best_confidence = match_confidence
                best_type = clause_pattern.clause_type

    return best_type, best_confidence


def assess_clause_risk(text: str, clause_type: ClauseType) -> ClauseRiskLevel:
    """Assess risk level of a clause based on content and type."""
    text_lower = text.lower()

    # High risk indicators
    high_risk_keywords = [
        "unlimited liability",
        "indemnif",
        "hold harmless",
        "penalty",
        "breach",
        "default",
        "termination for cause",
        "irrevocable",
        "waiver",
        "exclusive jurisdiction",
    ]

    # Critical risk indicators
    critical_risk_keywords = [
        "personal guarantee",
        "all assets",
        "unlimited",
        "joint and several",
        "cross-default",
        "acceleration",
    ]

    # Check for critical risks
    for keyword in critical_risk_keywords:
        if keyword in text_lower:
            return ClauseRiskLevel.CRITICAL

    # Check for high risks
    for keyword in high_risk_keywords:
        if keyword in text_lower:
            return ClauseRiskLevel.HIGH

    # Type-based risk assessment
    high_risk_types = {
        ClauseType.INDEMNITY,
        ClauseType.LIABILITY,
        ClauseType.TERMINATION,
    }
    if clause_type in high_risk_types:
        return ClauseRiskLevel.MEDIUM

    # Medium risk for obligations with restrictions
    if clause_type == ClauseType.OBLIGATION and "shall not" in text_lower:
        return ClauseRiskLevel.MEDIUM

    return ClauseRiskLevel.LOW


def segment_clauses(document: ProcessedDocument) -> ClauseSegmentationResult:
    """Segment a processed document into clauses.

    Analyzes text boundaries and classifies each clause.
    """
    start_time = time.time()
    all_clauses = []

    for page in document.pages:
        boundaries = detect_clause_boundaries(page.text)

        for i, start in enumerate(boundaries):
            # End is next boundary or end of text
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(page.text)

            clause_text = page.text[start:end].strip()

            if len(clause_text) < 10:  # Skip very short clauses
                continue

            # Classify clause
            clause_type, confidence = classify_clause(clause_text)

            # Assess risk
            risk_level = assess_clause_risk(clause_text, clause_type)

            clause = Clause(
                clause_id=f"{document.document_id}_p{page.page_number}_c{i}",
                text=clause_text,
                clause_type=clause_type,
                risk_level=risk_level,
                page_number=page.page_number,
                char_start=start,
                char_end=end,
                confidence=confidence,
            )
            all_clauses.append(clause)

    processing_time = (time.time() - start_time) * 1000

    return ClauseSegmentationResult(
        clauses=all_clauses,
        processing_time_ms=processing_time,
    )


async def segment_clauses_async(
    document: ProcessedDocument,
) -> ClauseSegmentationResult:
    """Async wrapper for clause segmentation."""
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, segment_clauses, document)
