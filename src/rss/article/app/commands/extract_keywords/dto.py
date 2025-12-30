"""DTOs para ExtractArticleKeywords command - Presentation Layer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ExtractKeywordsRequestDto:
    """
    DTO de request para extracción de keywords desde Presentation Layer.

    Mapea desde formatos de presentación (API, UI) a Command.
    """

    article_id: str

    # Configuración opcional
    max_keywords: Optional[int] = 10
    min_keyword_score: Optional[float] = 0.3
    include_ngrams: Optional[bool] = True
    language: Optional[str] = "auto"
    save_to_article: Optional[bool] = True
    override_existing: Optional[bool] = False

    # Metadata
    correlation_id: Optional[str] = None
    triggered_by: Optional[str] = "user"


@dataclass
class ExtractKeywordsResponseDto:
    """
    DTO de response para extracción de keywords hacia Presentation Layer.

    Mapea desde Result a formatos de presentación (API, UI).
    """

    success: bool
    article_id: str
    keywords: List[str] = field(default_factory=list)
    keyword_scores: Dict[str, float] = field(default_factory=dict)

    # Metadata
    extraction_method: str = "tfidf"
    total_keywords_found: int = 0
    keywords_saved: int = 0
    language_detected: Optional[str] = None

    # Error handling
    message: str = ""
    error_code: Optional[str] = None

    # Performance
    processing_time_ms: Optional[float] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def from_result(cls, result) -> "ExtractKeywordsResponseDto":
        """Factory method para crear desde KeywordExtractionResult."""
        return cls(
            success=result.success,
            article_id=result.article_id,
            keywords=result.keywords,
            keyword_scores=result.keyword_scores,
            extraction_method=result.extraction_method,
            total_keywords_found=result.total_keywords_found,
            keywords_saved=result.keywords_saved,
            language_detected=result.language_detected,
            message=result.message,
            error_code=result.error_code,
            processing_time_ms=result.processing_time_ms,
            timestamp=result.timestamp,
        )


@dataclass
class KeywordDto:
    """DTO para representar una keyword individual con metadata."""

    keyword: str
    score: float
    type: str = "unigram"  # unigram, bigram, trigram
    position: Optional[int] = None  # Posición en ranking

    @classmethod
    def from_keyword_and_score(
        cls, keyword: str, score: float, position: int
    ) -> "KeywordDto":
        """Factory method para crear desde keyword y score."""
        # Detectar tipo por espacios
        word_count = len(keyword.split())
        keyword_type = {
            1: "unigram",
            2: "bigram",
            3: "trigram",
        }.get(word_count, "phrase")

        return cls(
            keyword=keyword,
            score=score,
            type=keyword_type,
            position=position,
        )
