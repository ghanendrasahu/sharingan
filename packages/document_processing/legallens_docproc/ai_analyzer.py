"""AI analysis service for legal documents."""

from __future__ import annotations

import json
import time
import uuid
from typing import TYPE_CHECKING, Any

from legallens_docproc.analysis_models import (
    AIAnalysisResult,
    AnalysisType,
    DocumentSummary,
    KeyTerm,
    RiskFinding,
    RiskSeverity,
)
from legallens_docproc.prompts import (
    DOCUMENT_SUMMARY_PROMPT,
    KEY_TERMS_PROMPT,
    RISK_ASSESSMENT_PROMPT,
)

if TYPE_CHECKING:
    from legallens_docproc.clause_models import Clause


class AIAnalysisError(Exception):
    """Error during AI analysis."""

    def __init__(self, message: str, code: str = "ANALYSIS_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class LLMProvider:
    """Abstract LLM provider interface."""

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate text from prompt."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate text using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal AI assistant. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except ImportError as err:
            raise AIAnalysisError(
                "OpenAI package not installed. Install with: pip install openai",
                code="DEPENDENCY_ERROR",
            ) from err
        except Exception as e:
            raise AIAnalysisError(f"OpenAI API error: {e!s}", code="API_ERROR") from e


class GroqProvider(LLMProvider):
    """Groq LLM provider."""

    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768") -> None:
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate text using Groq API."""
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal AI assistant. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except ImportError as err:
            raise AIAnalysisError(
                "Groq package not installed. Install with: pip install groq",
                code="DEPENDENCY_ERROR",
            ) from err
        except Exception as e:
            raise AIAnalysisError(f"Groq API error: {e!s}", code="API_ERROR") from e


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate mock response."""
        return json.dumps(
            {
                "risk_level": "medium",
                "risk_score": 0.5,
                "issues": ["Sample issue for testing"],
                "recommendations": ["Sample recommendation"],
                "summary": "Mock analysis result for testing purposes.",
            }
        )


def get_llm_provider(
    provider: str = "openai",
    api_key: str = "",
    model: str = "gpt-4o",
) -> LLMProvider:
    """Get LLM provider by name."""
    providers = {
        "openai": lambda: OpenAIProvider(api_key=api_key, model=model),
        "groq": lambda: GroqProvider(api_key=api_key, model=model),
        "mock": MockProvider,
    }

    provider_factory = providers.get(provider)
    if provider_factory is None:
        raise AIAnalysisError(
            f"Unknown LLM provider: {provider}. Available: {list(providers.keys())}",
            code="INVALID_PROVIDER",
        )

    return provider_factory()


def _parse_json_response(response: str) -> dict[str, Any]:
    """Parse JSON response from LLM."""
    try:
        # Try to extract JSON from response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        else:
            json_str = response

        return json.loads(json_str.strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON response", "raw": response}


async def analyze_clause_risk(
    clause: Clause,
    document_context: str = "",
    provider: LLMProvider | None = None,
) -> RiskFinding:
    """Analyze risk of a single clause."""
    if provider is None:
        provider = MockProvider()

    prompt = RISK_ASSESSMENT_PROMPT.format(
        document_context=document_context,
        clause_text=clause.text,
    )

    response = await provider.generate(prompt)
    result = _parse_json_response(response)

    return RiskFinding(
        risk_id=f"risk_{uuid.uuid4().hex[:8]}",
        title=f"Risk in clause: {clause.clause_id}",
        description=result.get("summary", "Risk analysis completed"),
        severity=RiskSeverity(result.get("risk_level", "low")),
        clause_reference=clause.clause_id,
        recommendation=result.get("recommendations", ["Review clause"])[0]
        if result.get("recommendations")
        else "",
        confidence=result.get("risk_score", 0.5),
    )


async def analyze_document_summary(
    document_text: str,
    provider: LLMProvider | None = None,
) -> DocumentSummary:
    """Generate document summary using AI."""
    if provider is None:
        provider = MockProvider()

    # Truncate if too long
    truncated_text = document_text[:8000] if len(document_text) > 8000 else document_text

    prompt = DOCUMENT_SUMMARY_PROMPT.format(document_text=truncated_text)
    response = await provider.generate(prompt)
    result = _parse_json_response(response)

    return DocumentSummary(
        executive_summary=result.get("executive_summary", "Summary not available"),
        key_parties=result.get("key_parties", []),
        effective_date=result.get("effective_date"),
        termination_date=result.get("termination_date"),
        governing_law=result.get("governing_law"),
        total_value=result.get("total_value"),
        key_obligations=result.get("key_obligations", []),
        key_restrictions=result.get("key_restrictions", []),
    )


async def extract_key_terms(
    document_text: str,
    provider: LLMProvider | None = None,
) -> list[KeyTerm]:
    """Extract key terms from document using AI."""
    if provider is None:
        provider = MockProvider()

    truncated_text = document_text[:8000] if len(document_text) > 8000 else document_text

    prompt = KEY_TERMS_PROMPT.format(document_text=truncated_text)
    response = await provider.generate(prompt)
    result = _parse_json_response(response)

    terms = []
    for term_data in result.get("key_terms", []):
        terms.append(
            KeyTerm(
                term=term_data.get("term", ""),
                definition=term_data.get("definition"),
                section_reference=term_data.get("section_reference"),
            )
        )

    return terms


async def analyze_document_full(
    document_id: str,
    document_text: str,
    clauses: list[Clause],
    provider: LLMProvider | None = None,
    analysis_type: AnalysisType = AnalysisType.FULL_ANALYSIS,
) -> AIAnalysisResult:
    """Perform full AI analysis on a document."""
    start_time = time.time()

    if provider is None:
        provider = MockProvider()

    result = AIAnalysisResult(
        analysis_id=f"analysis_{uuid.uuid4().hex[:8]}",
        document_id=document_id,
        analysis_type=analysis_type,
    )

    try:
        # Generate summary
        summary = await analyze_document_summary(document_text, provider)
        result.summary = summary.executive_summary

        # Analyze key clauses for risks
        risk_findings = []
        for clause in clauses[:20]:  # Limit to 20 clauses
            risk = await analyze_clause_risk(clause, document_text[:2000], provider)
            risk_findings.append(risk)

        result.risk_findings = risk_findings

        # Calculate overall risk score
        if risk_findings:
            result.overall_risk_score = sum(r.confidence for r in risk_findings) / len(
                risk_findings
            )

        # Extract key terms
        result.key_terms = await extract_key_terms(document_text, provider)

        # Generate recommendations
        result.recommendations = [
            f"Review {len(risk_findings)} identified risk areas",
            "Consider legal counsel for high-risk clauses",
            "Ensure all parties understand key obligations",
        ]

    except Exception as e:
        result.error = f"Analysis failed: {e!s}"

    result.processing_time_ms = (time.time() - start_time) * 1000
    result.model_used = provider.__class__.__name__

    return result
