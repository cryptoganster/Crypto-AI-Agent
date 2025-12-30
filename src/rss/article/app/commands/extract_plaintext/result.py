"""Result para extracción de texto plano."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PlaintextExtractionResult:
    """
    Resultado de extracción de texto plano.

    INMUTABLE: Frozen dataclass siguiendo principios funcionales.
    """

    article_id: str
    success: bool
    plaintext_length: int
    word_count: int
    message: str
    error_code: Optional[str] = None
    processing_time_ms: Optional[float] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        plaintext_length: int,
        word_count: int,
        processing_time_ms: float,
    ) -> "PlaintextExtractionResult":
        """Factory method para resultado exitoso."""
        return cls(
            article_id=article_id,
            success=True,
            plaintext_length=plaintext_length,
            word_count=word_count,
            message=f"Plaintext extracted: {word_count} words, {plaintext_length} chars",
            processing_time_ms=processing_time_ms,
        )

    @classmethod
    def failure_result(
        cls,
        article_id: str,
        message: str,
        error_code: str,
    ) -> "PlaintextExtractionResult":
        """Factory method para resultado fallido."""
        return cls(
            article_id=article_id,
            success=False,
            plaintext_length=0,
            word_count=0,
            message=message,
            error_code=error_code,
        )

    @classmethod
    def skipped_result(
        cls,
        article_id: str,
        reason: str,
    ) -> "PlaintextExtractionResult":
        """Factory method para artículo omitido (ya tiene plaintext)."""
        return cls(
            article_id=article_id,
            success=True,
            plaintext_length=0,
            word_count=0,
            message=f"Skipped: {reason}",
            error_code="SKIPPED",
        )
