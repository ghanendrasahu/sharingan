"""Document classifier node."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from legallens_ai.state import AnalysisState

logger = logging.getLogger(__name__)


def classify_document(state: AnalysisState) -> dict[str, Any]:
    """Classify the document type using LLM.

    Node that determines what kind of legal document this is.
    """
    from legallens_ai.prompts import DOCUMENT_CLASSIFICATION_PROMPT

    document_text = state.get("document_text", "")
    if not document_text:
        return {
            "document_category": "unknown",
            "classification_confidence": 0.0,
        }

    # Use hint if provided
    if state.get("document_type_hint"):
        hint = state["document_type_hint"]
        if hint in ("employment", "nda", "lease", "vendor", "consultancy", "founder", "term_sheet"):
            return {
                "document_category": hint,
                "classification_confidence": 0.9,
            }

    # Truncate text for prompt
    truncated = document_text[:3000]
    prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(document_text=truncated)

    try:
        # Try to use LLM if available
        response = _call_llm(prompt)
        if response:
            result = _parse_json(response)
            return {
                "document_category": result.get("category", "unknown"),
                "classification_confidence": result.get("confidence", 0.5),
            }
    except Exception:
        logger.exception("LLM classification failed, using fallback")

    # Fallback: keyword-based classification
    category = _classify_by_keywords(document_text)
    return {
        "document_category": category,
        "classification_confidence": 0.6,
    }


def _classify_by_keywords(text: str) -> str:
    """Simple keyword-based document classification."""
    text_lower = text.lower()

    # NDA indicators
    nda_keywords = ["non-disclosure", "confidential", "nda", "secret information", "proprietary"]
    if any(kw in text_lower for kw in nda_keywords):
        return "nda"

    # Employment indicators
    employment_keywords = [
        "employment",
        "employee",
        "employer",
        "salary",
        "compensation",
        "termination of employment",
    ]
    if any(kw in text_lower for kw in employment_keywords):
        return "employment"

    # Lease indicators
    lease_keywords = ["lease", "tenant", "landlord", "rent", "premises", "demised"]
    if any(kw in text_lower for kw in lease_keywords):
        return "lease"

    # Vendor indicators
    vendor_keywords = ["vendor", "supplier", "procurement", "purchase order", "goods and services"]
    if any(kw in text_lower for kw in vendor_keywords):
        return "vendor"

    # Consultancy indicators
    consultancy_keywords = [
        "consultant",
        "consultancy",
        "independent contractor",
        "professional services",
    ]
    if any(kw in text_lower for kw in consultancy_keywords):
        return "consultancy"

    # Founder indicators
    founder_keywords = ["founder", "co-founder", "equity", "vesting", "shareholders agreement"]
    if any(kw in text_lower for kw in founder_keywords):
        return "founder"

    # Term sheet indicators
    term_sheet_keywords = ["term sheet", "investment", "valuation", "series a", "funding round"]
    if any(kw in text_lower for kw in term_sheet_keywords):
        return "term_sheet"

    return "other"


def _call_llm(prompt: str) -> str | None:
    """Call LLM for classification. Returns None if unavailable."""
    import os

    # Try OpenAI
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if api_key:
        try:
            import asyncio

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key)

            async def _generate() -> str:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a legal document classifier. Respond in valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=500,
                )
                return response.choices[0].message.content or ""

            return asyncio.run(_generate())
        except Exception:
            logger.exception("OpenAI classification failed")

    # Try Groq
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            import asyncio

            from groq import AsyncGroq  # type: ignore[import-untyped]

            client = AsyncGroq(api_key=groq_key)

            async def _generate_groq() -> str:
                response = await client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a legal document classifier. Respond in valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=500,
                )
                return response.choices[0].message.content or ""

            return asyncio.run(_generate_groq())
        except Exception:
            logger.exception("Groq classification failed")

    return None


def _parse_json(response: str) -> dict[str, Any]:
    """Parse JSON from LLM response."""
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        else:
            json_str = response
        return json.loads(json_str.strip())
    except (json.JSONDecodeError, IndexError):
        return {}
