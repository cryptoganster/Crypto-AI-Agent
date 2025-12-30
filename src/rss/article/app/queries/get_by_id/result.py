"""Result para GetArticleByIdQuery."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.rss.article.domain.read_models import ArticleReadModel

# Alias para mantener compatibilidad con código existente
ArticleDTO = ArticleReadModel


@dataclass(frozen=True)
class GetArticleByIdResult:
    """
    Resultado de GetArticleByIdQuery.

    Patrón Result Object para manejar éxito/fallo de forma explícita.
    """

    success: bool
    article: Optional[ArticleReadModel] = None
    error_message: Optional[str] = None

    @classmethod
    def success_result(cls, article: ArticleReadModel) -> "GetArticleByIdResult":
        """Crea resultado exitoso."""
        return cls(success=True, article=article)

    @classmethod
    def not_found(cls, article_id: UUID) -> "GetArticleByIdResult":
        """Crea resultado cuando artículo no existe."""
        return cls(success=False, error_message=f"Article {article_id} not found")

    @classmethod
    def failure(cls, error_message: str) -> "GetArticleByIdResult":
        """Crea resultado de fallo genérico."""
        return cls(success=False, error_message=error_message)
