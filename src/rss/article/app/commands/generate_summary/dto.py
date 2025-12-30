"""DTOs para GenerateArticleSummary command."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateArticleSummaryRequestDto:
    """DTO de request para presentation layer."""

    article_id: str
    summary_length: int = 500
    force_regenerate: bool = False
    update_article: bool = True


@dataclass(frozen=True)
class GenerateArticleSummaryResponseDto:
    """DTO de response para presentation layer."""

    success: bool
    article_id: str
    summary: str
    summary_length: int
    was_updated: bool
    error_message: Optional[str] = None

    @classmethod
    def from_result(cls, result) -> "GenerateArticleSummaryResponseDto":
        """Crea DTO desde Result del handler."""
        return cls(
            success=result.success,
            article_id=str(result.article_id),
            summary=result.summary,
            summary_length=len(result.summary),
            was_updated=result.was_updated,
            error_message=result.error_message,
        )
