"""Interface para ArticlePlaintextExtractionService."""

from abc import ABC, abstractmethod

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article


class IArticlePlaintextExtractionService(ABC):
    """
    Interface para servicio de extracción de texto plano desde HTML.

    RESPONSABILIDAD ÚNICA: Extraer texto plano limpio desde HTML scrapeado.
    """

    @abstractmethod
    def extract_plaintext(self, article: Article) -> str:
        """
        Extrae texto plano limpio desde el artículo.

        FUENTE:
        - Usa content_vo.scrapped (HTML scrapeado vía Playwright o trafilatura)

        Args:
            article: Artículo con content_vo.scrapped disponible

        Returns:
            Texto plano sin tags HTML, listo para NLP

        Raises:
            ValueError: Si el artículo no tiene content_vo.scrapped
        """
        pass

    @abstractmethod
    def extract_plaintext_from_html(self, html_content: str) -> str:
        """
        Extrae texto plano limpio desde HTML directamente.

        Event-Driven Architecture:
        - Permite extraer plaintext sin necesidad del aggregate completo
        - Usado cuando el HTML viene del evento anterior

        Args:
            html_content: Contenido HTML a procesar

        Returns:
            Texto plano sin tags HTML, listo para NLP

        Raises:
            ValueError: Si el HTML está vacío o es inválido
        """
