"""Result para DetectDuplicateArticle command."""

from dataclasses import dataclass
from typing import List, Optional

from src.rss.article.domain.services import DuplicateMatch


@dataclass(frozen=True)
class DetectDuplicateArticleResult:
    """
    Result de detección de duplicados.

    Attributes:
        success: Si la detección fue exitosa
        article_id: ID del artículo verificado
        is_duplicate: Si se encontraron duplicados
        duplicates: Lista de artículos duplicados encontrados
        error: Mensaje de error si falló
    """

    success: bool
    article_id: str
    is_duplicate: bool
    duplicates: List[DuplicateMatch]
    error: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        duplicates: List[DuplicateMatch],
    ) -> "DetectDuplicateArticleResult":
        """Crea result exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            is_duplicate=len(duplicates) > 0,
            duplicates=duplicates,
            error=None,
        )

    @classmethod
    def failure(
        cls,
        article_id: str,
        error: str,
    ) -> "DetectDuplicateArticleResult":
        """Crea result fallido."""
        return cls(
            success=False,
            article_id=article_id,
            is_duplicate=False,
            duplicates=[],
            error=error,
        )
