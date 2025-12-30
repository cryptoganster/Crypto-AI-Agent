"""DTOs para respuestas de preparación de publicación."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class ArticleReadinessDTO:
    """DTO para información de preparación de un artículo individual."""

    article_id: str
    title: str
    is_ready: bool
    pending_validations: List[str]
    quality_score: Optional[float]
    has_content: bool
    has_summary: bool
    has_keywords: bool
    word_count: Optional[int]
    created_at: datetime


@dataclass(frozen=True)
class PublishingReadinessDTO:
    """DTO para verificación de preparación de un artículo específico."""

    article_id: str
    is_ready: bool
    pending_validations: List[str]
    quality_score: Optional[float]
    has_content: bool
    has_summary: bool
    has_keywords: bool
    word_count: Optional[int]
    readability_score: Optional[float]


@dataclass(frozen=True)
class ReadinessSummaryDTO:
    """DTO para resumen de preparación de artículos."""

    ready: int
    pending: int
    needs_work: int
    blocked: int
    total: int
