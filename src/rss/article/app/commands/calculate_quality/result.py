"""Result para CalculateArticleQuality command."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CalculateArticleQualityResult:
    """Resultado del cálculo de quality (score + level)."""

    success: bool
    article_id: str
    quality_score: Optional[float] = None
    quality_level: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        quality_score: float,
        quality_level: str,
    ) -> "CalculateArticleQualityResult":
        """Crea resultado exitoso con score y level."""
        return cls(
            success=True,
            article_id=article_id,
            quality_score=quality_score,
            quality_level=quality_level,
        )

    @classmethod
    def failure_result(
        cls,
        article_id: str,
        message: str,
        error_code: str = "QUALITY_CALCULATION_FAILED",
    ) -> "CalculateArticleQualityResult":
        """Crea resultado fallido."""
        return cls(
            success=False,
            article_id=article_id,
            error_message=message,
            error_code=error_code,
        )
