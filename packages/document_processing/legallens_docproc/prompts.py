"""Prompts for AI legal document analysis."""

RISK_ASSESSMENT_PROMPT = """You are a legal AI assistant specializing in Indian contract law.
Analyze the following legal document clause and assess its risk level.

Document Context:
{document_context}

Clause to Analyze:
{clause_text}

Provide your analysis in the following JSON format:
{{
    "risk_level": "low|medium|high|critical",
    "risk_score": 0.0 to 1.0,
    "issues": ["list of potential issues"],
    "recommendations": ["list of recommendations"],
    "summary": "brief risk summary"
}}

Focus on:
1. Unfavorable terms for the weaker party
2. Unreasonable obligations or restrictions
3. Missing protections
4. Ambiguous language
5. Compliance with Indian contract law
"""

DOCUMENT_SUMMARY_PROMPT = """You are a legal AI assistant. Provide a comprehensive summary of this legal document.

Document Text:
{document_text}

Provide your summary in the following JSON format:
{{
    "executive_summary": "2-3 sentence overview",
    "key_parties": ["list of parties involved"],
    "effective_date": "date if mentioned or null",
    "termination_date": "date if mentioned or null",
    "governing_law": "applicable law",
    "total_value": "monetary value if mentioned or null",
    "key_obligations": ["list of main obligations"],
    "key_restrictions": ["list of main restrictions"]
}}
"""

CLAUSE_CLASSIFICATION_PROMPT = """You are a legal AI assistant. Classify the following legal clause.

Clause Text:
{clause_text}

Classify this clause into one of these categories:
- definition: Term definitions
- obligation: Required actions
- right: Permitted actions
- restriction: Prohibited actions
- condition: Conditions precedent
- remedy: Remedies for breach
- indemnity: Indemnification clauses
- termination: Contract termination
- confidentiality: Non-disclosure terms
- ip_rights: Intellectual property
- liability: Limitation of liability
- dispute_resolution: Arbitration/mediation
- governing_law: Applicable law

Provide your classification in the following JSON format:
{{
    "clause_type": "category",
    "confidence": 0.0 to 1.0,
    "summary": "brief description of the clause"
}}
"""

COMPLIANCE_CHECK_PROMPT = """You are a legal AI assistant specializing in Indian regulatory compliance.
Check if the following document complies with relevant Indian laws.

Document Text:
{document_text}

Relevant Laws to Check:
{relevant_laws}

Provide your compliance check in the following JSON format:
{{
    "compliant": true or false,
    "issues": [
        {{
            "law": "law name",
            "issue": "description of non-compliance",
            "severity": "low|medium|high|critical",
            "recommendation": "how to fix"
        }}
    ],
    "summary": "overall compliance summary"
}}
"""

KEY_TERMS_PROMPT = """You are a legal AI assistant. Extract key terms and definitions from this legal document.

Document Text:
{document_text}

Provide your extraction in the following JSON format:
{{
    "key_terms": [
        {{
            "term": "term name",
            "definition": "definition if found or null",
            "section_reference": "section/clause reference"
        }}
    ]
}}

Focus on:
1. Defined terms (those in quotes or "means" definitions)
2. Important legal concepts
3. Technical terms
4. Names of parties, products, or services
"""
