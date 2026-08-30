"""LLM service for AI-powered features."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient:
    """Simple LLM client supporting OpenAI and Groq."""

    def __init__(self):
        self._client = None
        self._provider = None

    def _initialize(self):
        """Initialize LLM client on demand."""
        if self._client is not None:
            return

        import os

        # Try OpenAI first
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=openai_key)
                self._provider = "openai"
                logger.info("Initialized OpenAI client")
                return
            except ImportError:
                pass

        # Try Groq
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import AsyncGroq  # type: ignore[import-untyped]

                self._client = AsyncGroq(api_key=groq_key)
                self._provider = "groq"
                logger.info("Initialized Groq client")
                return
            except ImportError:
                pass

        logger.warning("No LLM provider configured")

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        """Complete a prompt using LLM."""
        self._initialize()

        if self._client is None:
            return {"text": "LLM not configured", "confidence": 0.0}

        try:
            if self._provider == "openai":
                response = await self._client.chat.completions.create(
                    model=model or "gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return {
                    "text": response.choices[0].message.content or "",
                    "confidence": 0.8,
                }
            elif self._provider == "groq":
                response = await self._client.chat.completions.create(
                    model=model or "llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return {
                    "text": response.choices[0].message.content or "",
                    "confidence": 0.7,
                }
        except Exception:
            logger.exception("LLM completion failed")

        return {"text": "Error calling LLM", "confidence": 0.0}


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
