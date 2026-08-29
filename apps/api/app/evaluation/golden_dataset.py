"""Golden dataset for AI evaluation."""

from __future__ import annotations

from typing import Any


class GoldenDataset:
    """Golden dataset for evaluating AI analysis quality."""

    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []
        self._clauses: list[dict[str, Any]] = []
        self._risks: list[dict[str, Any]] = []

    def add_document(
        self,
        doc_id: str,
        content: str,
        expected_clauses: list[str],
        expected_risks: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a document to the golden dataset."""
        self._documents.append(
            {
                "doc_id": doc_id,
                "content": content,
                "expected_clauses": expected_clauses,
                "expected_risks": expected_risks,
                "metadata": metadata or {},
            }
        )

    def add_clause(
        self,
        clause_id: str,
        text: str,
        expected_type: str,
        expected_risk_level: str,
    ) -> None:
        """Add a clause to the golden dataset."""
        self._clauses.append(
            {
                "clause_id": clause_id,
                "text": text,
                "expected_type": expected_type,
                "expected_risk_level": expected_risk_level,
            }
        )

    def add_risk(
        self,
        risk_id: str,
        clause_id: str,
        risk_type: str,
        severity: str,
        description: str,
    ) -> None:
        """Add a risk to the golden dataset."""
        self._risks.append(
            {
                "risk_id": risk_id,
                "clause_id": clause_id,
                "risk_type": risk_type,
                "severity": severity,
                "description": description,
            }
        )

    def get_documents(self) -> list[dict[str, Any]]:
        """Get all documents in the dataset."""
        return self._documents.copy()

    def get_clauses(self) -> list[dict[str, Any]]:
        """Get all clauses in the dataset."""
        return self._clauses.copy()

    def get_risks(self) -> list[dict[str, Any]]:
        """Get all risks in the dataset."""
        return self._risks.copy()

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get a specific document by ID."""
        for doc in self._documents:
            if doc["doc_id"] == doc_id:
                return doc
        return None

    def size(self) -> dict[str, int]:
        """Get dataset size."""
        return {
            "documents": len(self._documents),
            "clauses": len(self._clauses),
            "risks": len(self._risks),
        }


def create_sample_dataset() -> GoldenDataset:
    """Create a sample golden dataset for testing."""
    dataset = GoldenDataset()

    # Sample employment agreement
    dataset.add_document(
        doc_id="employment_001",
        content="""
        EMPLOYMENT AGREEMENT

        This Employment Agreement is entered into between Company XYZ ("Employer")
        and John Doe ("Employee").

        1. TERM: This agreement shall commence on January 1, 2024 and continue
        for a period of 24 months unless terminated earlier.

        2. COMPENSATION: Employee shall receive a base salary of ₹500,000 per annum,
        payable monthly.

        3. TERMINATION: Either party may terminate this agreement with 30 days
        written notice. Employer may terminate immediately for cause.

        4. CONFIDENTIALITY: Employee agrees to maintain confidentiality of all
        proprietary information for 2 years after termination.

        5. NON-COMPETE: Employee shall not engage in competing business for
        12 months after termination within 50km radius.
        """,
        expected_clauses=[
            "term",
            "compensation",
            "termination",
            "confidentiality",
            "non_compete",
        ],
        expected_risks=["excessive_non_compete", "unilateral_termination"],
    )

    # Sample service agreement
    dataset.add_document(
        doc_id="service_001",
        content="""
        SERVICE AGREEMENT

        This Service Agreement is between Client ABC ("Client") and
        Service Provider DEF ("Provider").

        1. SERVICES: Provider shall deliver software development services
        as described in Exhibit A.

        2. PAYMENT: Client shall pay ₹100,000 per month, due within 30 days
        of invoice.

        3. LIABILITY: Provider's total liability shall not exceed the total
        fees paid under this agreement.

        4. INTELLECTUAL PROPERTY: All work product shall be owned by Client.

        5. TERM: Agreement shall be effective for 12 months.
        """,
        expected_clauses=["services", "payment", "liability", "ip", "term"],
        expected_risks=["limited_liability"],
    )

    # Sample clauses
    dataset.add_clause(
        clause_id="non_compete_001",
        text="Employee shall not engage in competing business for 12 months after termination within 50km radius.",
        expected_type="non_compete",
        expected_risk_level="high",
    )

    dataset.add_clause(
        clause_id="termination_001",
        text="Either party may terminate this agreement with 30 days written notice.",
        expected_type="termination",
        expected_risk_level="low",
    )

    dataset.add_clause(
        clause_id="liability_001",
        text="Provider's total liability shall not exceed the total fees paid under this agreement.",
        expected_type="limitation_of_liability",
        expected_risk_level="medium",
    )

    # Sample risks
    dataset.add_risk(
        risk_id="risk_non_compete_001",
        clause_id="non_compete_001",
        risk_type="excessive_restrictive_covenant",
        severity="high",
        description="Non-compete clause is overly restrictive with 12 months and 50km radius",
    )

    dataset.add_risk(
        risk_id="risk_termination_001",
        clause_id="termination_001",
        risk_type="unilateral_termination",
        severity="medium",
        description="Termination clause allows unilateral termination with short notice",
    )

    return dataset
