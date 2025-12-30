"""Result para ExtractArticleKeywords command con factory methods."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class KeywordExtractionResult:
    """
    Resultado de la extracción de keywords de un artículo.

    Value Object inmutable con factory methods para casos comunes.
    """

    # Resultado principal
    success: bool
    article_id: str

    # Keywords extraídas
    keywords: List[str] = field(default_factory=list)
    keyword_scores: Dict[str, float] = field(default_factory=dict)  # keyword -> score

    # Metadata de extracción
    extraction_method: str = "tfidf"  # tfidf, yake, textrank
    total_keywords_found: int = 0
    keywords_saved: int = 0
    language_detected: Optional[str] = None
    language_confidence: Optional[float] = None  # 0.0-1.0

    # Análisis de relevancia
    highly_relevant_count: int = 0  # Keywords con score > 0.7
    moderately_relevant_count: int = 0  # Keywords con score 0.4-0.7

    # Información adicional
    message: str = ""
    error_code: Optional[str] = None
    processing_time_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Factory methods
    @classmethod
    def success_result(
        cls,
        article_id: str,
        keywords: List[str],
        keyword_scores: Dict[str, float],
        extraction_method: str = "tfidf",
        language_detected: Optional[str] = None,
        language_confidence: Optional[float] = None,
        keywords_saved: int = 0,
        processing_time_ms: Optional[float] = None,
        highly_relevant_count: int = 0,
        moderately_relevant_count: int = 0,
    ) -> "KeywordExtractionResult":
        """Factory method para resultado exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            keywords=keywords,
            keyword_scores=keyword_scores,
            extraction_method=extraction_method,
            total_keywords_found=len(keywords),
            keywords_saved=keywords_saved,
            language_detected=language_detected,
            language_confidence=language_confidence,
            highly_relevant_count=highly_relevant_count,
            moderately_relevant_count=moderately_relevant_count,
            message=f"Keywords extraídas exitosamente: {len(keywords)} keywords ({highly_relevant_count} alta relevancia)",
            processing_time_ms=processing_time_ms,
        )

    @classmethod
    def failure_result(
        cls,
        article_id: str,
        message: str,
        error_code: str = "EXTRACTION_ERROR",
    ) -> "KeywordExtractionResult":
        """Factory method para resultado fallido."""
        return cls(
            success=False,
            article_id=article_id,
            message=message,
            error_code=error_code,
        )

    @classmethod
    def article_not_found(cls, article_id: str) -> "KeywordExtractionResult":
        """Factory method para artículo no encontrado."""
        return cls(
            success=False,
            article_id=article_id,
            message=f"Artículo {article_id} no encontrado",
            error_code="ARTICLE_NOT_FOUND",
        )

    @classmethod
    def insufficient_content(cls, article_id: str) -> "KeywordExtractionResult":
        """Factory method para contenido insuficiente."""
        return cls(
            success=False,
            article_id=article_id,
            message="Contenido insuficiente para extraer keywords",
            error_code="INSUFFICIENT_CONTENT",
        )

    @classmethod
    def no_keywords_found(cls, article_id: str) -> "KeywordExtractionResult":
        """Factory method para cuando no se encuentran keywords."""
        return cls(
            success=True,
            article_id=article_id,
            keywords=[],
            keyword_scores={},
            message="No se encontraron keywords relevantes",
        )
