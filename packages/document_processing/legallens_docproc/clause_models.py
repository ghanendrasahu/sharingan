"""Clause segmentation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ClauseType(StrEnum):
    """Types of legal clauses."""

    DEFINITION = "definition"
    OBLIGATION = "obligation"
    RIGHT = "right"
    RESTRICTION = "restriction"
    CONDITION = "condition"
    REMEDY = "remedy"
    INDEMNITY = "indemnity"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    IP_RIGHTS = "ip_rights"
    LIABILITY = "liability"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    OTHER = "other"


class ClauseRiskLevel(StrEnum):
    """Risk levels for clauses."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Clause:
    """A single clause from a document."""

    clause_id: str
    text: str
    clause_type: ClauseType = ClauseType.OTHER
    risk_level: ClauseRiskLevel | None = None
    page_number: int | None = None
    char_start: int = 0
    char_end: int = 0
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.char_end = self.char_start + len(self.text)

    @property
    def word_count(self) -> int:
        """Count words in clause."""
        return len(self.text.split()) if self.text else 0

    @property
    def char_count(self) -> int:
        """Count characters in clause."""
        return len(self.text)


@dataclass
class ClauseSegmentationResult:
    """Result of clause segmentation."""

    clauses: list[Clause] = field(default_factory=list)
    total_clauses: int = 0
    total_chars: int = 0
    processing_time_ms: float | None = None
    error: str | None = None

    def __post_init__(self):
        self.total_clauses = len(self.clauses)
        self.total_chars = sum(c.char_count for c in self.clauses)

    def get_clauses_by_type(self, clause_type: ClauseType) -> list[Clause]:
        """Get clauses filtered by type."""
        return [c for c in self.clauses if c.clause_type == clause_type]

    def get_clauses_by_risk(self, risk_level: ClauseRiskLevel) -> list[Clause]:
        """Get clauses filtered by risk level."""
        return [c for c in self.clauses if c.risk_level == risk_level]

    def get_high_risk_clauses(self) -> list[Clause]:
        """Get high and critical risk clauses."""
        return [
            c
            for c in self.clauses
            if c.risk_level in (ClauseRiskLevel.HIGH, ClauseRiskLevel.CRITICAL)
        ]
