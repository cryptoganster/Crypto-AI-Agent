"""DTOs para DetectArticleLanguageCommand (Presentation Layer)."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class DetectArticleLanguageRequestDto:
    """
    DTO de request para presentation layer.

    Datos primitivos para facilitar serialización.
    """

    article_id: str  # String para JSON serialization
    override_existing: bool = False
    correlation_id: str = ""
    triggered_by: str = "system"


@dataclass
class DetectArticleLanguageResponseDto:
    """
    DTO de response para presentation layer.

    Datos primitivos serializables a JSON.
    """

    success: bool
    article_id: str
    language_detected: Optional[str] = None
    confidence: float = 0.0
    language_saved: bool = False
    message: str = ""
    error_code: Optional[str] = None
    processing_time_ms: float = 0.0
