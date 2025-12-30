"""Interface para ArticleLanguageDetectionService."""

from abc import ABC, abstractmethod

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.value_objects.metadata import ArticleLanguage


class IArticleLanguageDetectionService(ABC):
    """
    Interface para servicio de detección de idioma de artículos.

    RESPONSABILIDAD ÚNICA: Detectar idioma del contenido del artículo.
    Separado de ArticleKeywordService para adherir a SRP.
    """

    @abstractmethod
    def detect_language(self, article: Article) -> ArticleLanguage:
        """
        Detecta el idioma del artículo usando análisis de stopwords.

        Args:
            article: Artículo a analizar (requiere content_markdown)

        Returns:
            ContentLanguage con código de idioma y nivel de confianza
        """
        pass
