"""Embedding service for generating vector embeddings."""

from __future__ import annotations

import hashlib

from legallens_docproc.embedding_models import (
    EmbeddingBatchResult,
    EmbeddingResult,
)


class EmbeddingError(Exception):
    """Error during embedding generation."""

    def __init__(self, message: str, code: str = "EMBEDDING_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class EmbeddingProviderABC:
    """Abstract base class for embedding providers."""

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text."""
        raise NotImplementedError

    async def embed_texts(self, texts: list[str]) -> EmbeddingBatchResult:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if the provider is available."""
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProviderABC):
    """OpenAI embedding provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
            )

            return EmbeddingResult(
                embedding=response.data[0].embedding,
                model=self.model,
                dimensions=self.dimensions,
                tokens_used=response.usage.total_tokens,
            )
        except ImportError as err:
            raise EmbeddingError(
                "OpenAI package not installed. Install with: pip install openai",
                code="DEPENDENCY_ERROR",
            ) from err
        except Exception as e:
            raise EmbeddingError(f"OpenAI embedding error: {e!s}", code="API_ERROR") from e

    async def embed_texts(self, texts: list[str]) -> EmbeddingBatchResult:
        """Generate embeddings for multiple texts."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )

            embeddings = []
            total_tokens = 0

            for data in response.data:
                embeddings.append(
                    EmbeddingResult(
                        embedding=data.embedding,
                        model=self.model,
                        dimensions=self.dimensions,
                    )
                )

            total_tokens = response.usage.total_tokens

            return EmbeddingBatchResult(
                embeddings=embeddings,
                total_tokens=total_tokens,
            )
        except ImportError as err:
            raise EmbeddingError(
                "OpenAI package not installed. Install with: pip install openai",
                code="DEPENDENCY_ERROR",
            ) from err
        except Exception as e:
            raise EmbeddingError(f"OpenAI batch embedding error: {e!s}", code="API_ERROR") from e

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return bool(self.api_key)


class MockEmbeddingProvider(EmbeddingProviderABC):
    """Mock embedding provider for testing."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate mock embedding."""
        # Generate deterministic embedding from text hash
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest()[:8], 16)

        import random

        rng = random.Random(seed)
        embedding = [rng.random() for _ in range(self.dimensions)]

        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]

        return EmbeddingResult(
            embedding=embedding,
            model="mock-embedding",
            dimensions=self.dimensions,
            tokens_used=len(text.split()),
        )

    async def embed_texts(self, texts: list[str]) -> EmbeddingBatchResult:
        """Generate mock embeddings for multiple texts."""
        embeddings = []
        total_tokens = 0

        for text in texts:
            result = await self.embed_text(text)
            embeddings.append(result)
            total_tokens += result.tokens_used

        return EmbeddingBatchResult(
            embeddings=embeddings,
            total_tokens=total_tokens,
        )

    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True


def get_embedding_provider(
    provider: str = "openai",
    api_key: str = "",
    model: str = "text-embedding-3-small",
    dimensions: int = 1536,
) -> EmbeddingProviderABC:
    """Get embedding provider by name."""
    providers = {
        "openai": lambda: OpenAIEmbeddingProvider(
            api_key=api_key, model=model, dimensions=dimensions
        ),
        "mock": lambda: MockEmbeddingProvider(dimensions=dimensions),
    }

    provider_factory = providers.get(provider)
    if provider_factory is None:
        raise EmbeddingError(
            f"Unknown embedding provider: {provider}. Available: {list(providers.keys())}",
            code="INVALID_PROVIDER",
        )

    return provider_factory()
