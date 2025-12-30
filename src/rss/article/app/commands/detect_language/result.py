"""Result para DetectArticleLanguageCommand."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class LanguageDetectionResult:
    """
    Result de detección de idioma.

    Contiene idioma detectado, confianza y si fue guardado.
    """

    success: bool
    article_id: UUID
    language_detected: Optional[str] = None  # "es", "en", "fr", etc.
    confidence: float = 0.0  # 0.0-1.0
    language_saved: bool = False
    message: str = ""
    error_code: Optional[str] = None
    processing_time_ms: float = 0.0

    @classmethod
    def success_result(
        cls,
        article_id: UUID,
        language_detected: str,
        confidence: float,
        language_saved: bool,
        processing_time_ms: float,
    ) -> "LanguageDetectionResult":
        """Factory method para resultado exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            language_detected=language_detected,
            confidence=confidence,
            language_saved=language_saved,
            message=f"Idioma detectado: {language_detected.upper()} ({confidence:.1%} confianza)",
            processing_time_ms=processing_time_ms,
        )

    @classmethod
    def article_not_found(cls, article_id: UUID) -> "LanguageDetectionResult":
        """Factory method cuando artículo no existe."""
        return cls(
            success=False,
            article_id=article_id,
            message=f"Artículo {article_id} no encontrado",
            error_code="ARTICLE_NOT_FOUND",
        )

    @classmethod
    def insufficient_content(cls, article_id: UUID) -> "LanguageDetectionResult":
        """Factory method cuando no hay suficiente contenido."""
        return cls(
            success=False,
            article_id=article_id,
            message="Contenido insuficiente para detectar idioma",
            error_code="INSUFFICIENT_CONTENT",
        )

    @classmethod
    def failure_result(
        cls,
        article_id: UUID,
        message: str,
        error_code: str,
    ) -> "LanguageDetectionResult":
        """Factory method para error genérico."""
        return cls(
            success=False,
            article_id=article_id,
            message=message,
            error_code=error_code,
        )
