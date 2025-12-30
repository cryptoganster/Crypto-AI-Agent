"""Interface para ArticleContentExtractionService."""

from typing import Protocol

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article


class IArticleContentExtractionService(Protocol):
    """
    Interface para servicio de extracción de summary.

    Dependency Inversion Principle: Application layer depende de esta abstracción.
    """

    # Configuración por defecto
    DEFAULT_SUMMARY_LENGTH: int = 500

    def generate_summary(
        self, article: Article, max_length: int = DEFAULT_SUMMARY_LENGTH
    ) -> str:
        """
        Genera un summary (resumen) del artículo.

        Args:
            article: Artículo del que extraer summary
            max_length: Longitud máxima del summary en caracteres

        Returns:
            Summary del artículo
        """
        ...
