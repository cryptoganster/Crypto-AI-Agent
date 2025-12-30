"""Interface para conversión HTML a Markdown - Article Bounded Context."""

from typing import Protocol


class IHtmlToMarkdownConverter(Protocol):
    """
    Interface para convertir HTML a Markdown.

    Domain Interface PURA - sin dependencias de infraestructura.

    Responsabilidades:
    - Convertir HTML limpio a formato Markdown
    - Mantener estructura de contenido (headers, listas, énfasis)
    - Generar versiones con y sin URLs para diferentes propósitos

    Implementaciones concretas:
    - HtmlToMarkdownConverter (usando markdownify)
    """

    def convert_with_links(self, html_content: str) -> str:
        """
        Convierte contenido HTML a formato Markdown preservando links.

        Uso: Contenido principal para lectura humana.

        Args:
            html_content: Contenido HTML a convertir

        Returns:
            Contenido en formato Markdown con links [text](url)

        Raises:
            ValueError: Si el contenido está vacío o la conversión falla
        """
        ...

    def convert_without_links(self, html_content: str) -> str:
        """
        Convierte contenido HTML a formato Markdown removiendo links.

        Uso: Procesamiento AI/ML donde URLs no aportan valor semántico.
        Los links se convierten solo a su texto: [text](url) → text

        Args:
            html_content: Contenido HTML a convertir

        Returns:
            Contenido en formato Markdown sin links

        Raises:
            ValueError: Si el contenido está vacío o la conversión falla
        """
        ...
