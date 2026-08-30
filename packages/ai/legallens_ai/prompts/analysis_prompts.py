"""Prompts for legal document analysis."""

DOCUMENT_CLASSIFICATION_PROMPT = """You are a legal document classifier. Classify the following document into one of these categories:
- employment: Employment agreements, offer letters, service contracts
- nda: Non-disclosure agreements, confidentiality agreements
- lease: Property lease agreements, rental agreements
- vendor: Vendor/supplier agreements, procurement contracts
- consultancy: Consultancy agreements, independent contractor agreements
- founder: Founder agreements, co-founder contracts
- term_sheet: Term sheets, investment agreements
- other: Other legal documents
- unknown: Cannot determine document type

Document text (first 3000 chars):
{document_text}

Respond with JSON:
{{
    "category": "<category>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}"""

RISK_ANALYSIS_PROMPT = """You are a legal risk analyst specializing in Indian law. Analyze the following clause for legal risks.

Document context (first 2000 chars):
{document_context}

Clause to analyze:
{clause_text}

Identify ALL risks in this clause. For each risk, provide:
1. A clear title
2. Detailed description of the risk
3. Severity: low, medium, high, or critical
4. Recommendation to mitigate
5. Confidence score (0.0-1.0)

Consider these risk categories:
- Legal compliance risks (Indian Contract Act, IT Act, etc.)
- Financial risks (penalties, liability exposure)
- Intellectual property risks
- Confidentiality risks
- Privacy/data protection risks
- Operational risks
- Reputational risks

Respond with JSON:
{{
    "risks": [
        {{
            "title": "<risk title>",
            "description": "<detailed description>",
            "severity": "<low|medium|high|critical>",
            "recommendation": "<mitigation recommendation>",
            "confidence": <0.0-1.0>,
            "legal_source": "<relevant law/section if applicable>"
        }}
    ]
}}"""

MISSING_CLAUSE_PROMPT = """You are a legal document reviewer. Analyze whether this {document_type} document is missing any important clauses.

Document text (first 3000 chars):
{document_text}

Existing clauses found:
{existing_clauses}

For a standard {document_type} agreement in India, identify any MISSING clauses that should be present. Consider:
- Standard protective clauses for this document type
- Indian legal requirements
- Best practices for this type of agreement
- Common clauses that protect parties

For each missing clause, provide:
1. Clause name
2. Why it's important
3. Importance level: critical, important, or recommended
4. Example drafting language

Respond with JSON:
{{
    "missing_clauses": [
        {{
            "clause_name": "<name>",
            "description": "<why it's important>",
            "importance": "<critical|important|recommended>",
            "clause_type": "<type of clause>",
            "example_drafting": "<example clause text>",
            "confidence": <0.0-1.0>
        }}
    ]
}}"""

EVIDENCE_VERIFICATION_PROMPT = """You are a legal citation verifier. Verify whether the following legal claims are supported by actual Indian law.

Claims to verify:
{claims}

For each claim, determine:
1. Is there a relevant Indian law or regulation that supports this claim?
2. What is the specific source (act name, section number)?
3. Does the source actually support the claim?
4. Confidence level

Known Indian legal sources:
- Indian Contract Act, 1872 (Sections 1-238)
- Companies Act, 2013
- Information Technology Act, 2000
- Arbitration and Conciliation Act, 1996
- Digital Personal Data Protection Act, 2023
- Indian Penal Code, 1860
- Specific Relief Act, 1963

Respond with JSON:
{{
    "verified_citations": [
        {{
            "claim": "<original claim>",
            "citation": "<specific law/section>",
            "source": "<act name>",
            "section": "<section number>",
            "supports_claim": <true|false>,
            "confidence": <0.0-1.0>
        }}
    ]
}}"""

RECOMMENDATION_PROMPT = """You are a legal advisor for Indian startups. Based on the following analysis, provide practical recommendations.

Document type: {document_type}
Risk score: {risk_score}/100
Risk band: {risk_band}

Risks identified:
{risks_summary}

Missing clauses:
{missing_clauses_summary}

Provide 3-7 actionable recommendations. Focus on:
1. Most critical issues to address immediately
2. Specific clause modifications suggested
3. Indian legal compliance steps
4. Risk mitigation strategies

Respond with JSON:
{{
    "recommendations": [
        "<recommendation 1>",
        "<recommendation 2>"
    ]
}}"""

EXECUTIVE_SUMMARY_PROMPT = """You are a legal analyst. Create a concise executive summary of this legal document analysis.

Document type: {document_type}
Overall risk score: {risk_score}/100

Key findings:
{key_findings}

Provide a 2-3 sentence executive summary suitable for a business user who needs to understand the key risks and obligations at a glance.

Respond with JSON:
{{
    "executive_summary": "<summary text>",
    "key_parties": ["<party 1>", "<party 2>"],
    "key_obligations": ["<obligation 1>", "<obligation 2>"],
    "key_restrictions": ["<restriction 1>", "<restriction 2>"]
}}"""
