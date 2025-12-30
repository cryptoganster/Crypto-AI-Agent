"""Domain Service para extracción de texto plano desde HTML."""

from typing import Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.external import IHtmlToPlaintextConverter
from src.rss.article.domain.interfaces.services.plaintext_extraction import (
    IArticlePlaintextExtractionService,
)


class ArticlePlaintextExtractionService(IArticlePlaintextExtractionService):
    """
    Servicio de dominio para extracción de texto plano.

    RESPONSABILIDAD ÚNICA: Extraer texto plano limpio desde HTML scrapeado.

    ARQUITECTURA:
    - Inyecta IHtmlToPlaintextConverter (Dependency Inversion)
    - NO conoce implementaciones concretas (BeautifulSoup, html2text, etc.)
    - Domain Service puro con lógica de dominio
    - Facilita testing con mocks

    USO EN PIPELINE:
    - Fase 2: content_scrapped → content_plaintext
    - Prepara texto para NLP (idioma, keywords, sentimiento)
    """

    def __init__(self, html_converter: Optional[IHtmlToPlaintextConverter]):
        """
        Inicializa el servicio con un converter inyectado.

        Args:
            html_converter: Implementación de IHtmlToPlaintextConverter
        """
        self._html_converter = html_converter

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
        if not article.content.scraped:
            raise ValueError(
                f"Article {article.id} must have content_vo.scraped to extract plaintext"
            )

        # Verificar que el converter esté disponible
        if self._html_converter is None:
            raise ValueError("HTML converter not configured")

        # Delegar conversión al adapter inyectado
        return self._html_converter.convert(article.content.scraped)

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
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")

        # Verificar que el converter esté disponible
        if self._html_converter is None:
            raise ValueError("HTML converter not configured")

        # Delegar conversión al adapter inyectado
        return self._html_converter.convert(html_content)
