"""Interface para conversión de HTML a texto plano - Article Bounded Context."""

from typing import Protocol


class IHtmlToPlaintextConverter(Protocol):
    """
    Interface para convertir HTML a texto plano limpio.

    DEPENDENCY INVERSION PRINCIPLE:
    - Domain layer define la interface
    - Infrastructure layer implementa el adapter concreto

    USO EN NLP:
    - Detección de idioma (fastText necesita texto puro)
    - Extracción de keywords (sin URLs, tags HTML)
    - Análisis de sentimiento

    Implementaciones concretas:
    - BeautifulSoupPlaintextConverter
    """

    def convert(self, html_content: str) -> str:
        """
        Convierte contenido HTML a texto plano limpio.

        Args:
            html_content: HTML scrapeado

        Returns:
            Texto plano sin tags, URLs inline, imágenes, scripts, styles

        Example:
            >>> converter.convert('<p>Hello <strong>world</strong></p>')
            'Hello world'
        """
        ...
