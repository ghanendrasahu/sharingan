"""OCR provider abstraction for scanned documents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OCRResult:
    """Result of OCR processing."""

    text: str
    confidence: float | None = None
    language: str | None = None
    error: str | None = None


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""

    @abstractmethod
    async def recognize_text(self, image_data: bytes) -> OCRResult:
        """Recognize text from image data."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        ...


class TesseractOCR(OCRProvider):
    """Tesseract OCR provider."""

    def __init__(self, language: str = "eng") -> None:
        self.language = language

    async def recognize_text(self, image_data: bytes) -> OCRResult:
        """Recognize text using Tesseract."""
        try:
            from io import BytesIO

            import pytesseract
            from PIL import Image

            image = Image.open(BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang=self.language)
            confidence_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [int(c) for c in confidence_data["conf"] if c != "-1"]
            avg_confidence = sum(confidences) / len(confidences) if confidences else None

            return OCRResult(
                text=text,
                confidence=avg_confidence / 100.0 if avg_confidence else None,
                language=self.language,
            )
        except ImportError:
            return OCRResult(
                error="Tesseract not installed. Install with: pip install pytesseract pillow"
            )
        except Exception as e:
            return OCRResult(error=f"Tesseract OCR failed: {e!s}")

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False


class MockOCR(OCRProvider):
    """Mock OCR provider for testing."""

    async def recognize_text(self, image_data: bytes) -> OCRResult:
        """Return mock OCR result."""
        return OCRResult(
            text="[OCR text would appear here]",
            confidence=0.95,
            language="eng",
        )

    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True


def get_ocr_provider(provider: str = "tesseract") -> OCRProvider:
    """Get OCR provider by name."""
    providers = {
        "tesseract": TesseractOCR,
        "mock": MockOCR,
    }

    provider_class = providers.get(provider)
    if provider_class is None:
        raise ValueError(f"Unknown OCR provider: {provider}. Available: {list(providers.keys())}")

    return provider_class()
