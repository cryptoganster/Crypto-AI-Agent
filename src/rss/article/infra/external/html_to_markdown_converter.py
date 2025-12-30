"""HTML to Markdown converter - Article Bounded Context."""

import re

from markdownify import markdownify as md

from src.rss.article.domain.interfaces.external import IHtmlToMarkdownConverter


class HtmlToMarkdownConverter(IHtmlToMarkdownConverter):
    """
    Converter de HTML a Markdown usando markdownify.

    Proporciona dos métodos de conversión:
    - convert_with_links: Preserva links para lectura humana
    - convert_without_links: Remueve links para procesamiento AI/ML
    """

    def convert_with_links(self, html_content: str) -> str:
        """
        Convierte HTML a Markdown preservando links.

        Uso: Contenido principal para lectura humana.
        """
        return self._convert(html_content, strip_links=False)

    def convert_without_links(self, html_content: str) -> str:
        """
        Convierte HTML a Markdown removiendo links.

        Uso: Procesamiento AI/ML donde URLs no aportan valor semántico.
        Los links se convierten solo a su texto: [text](url) → text
        """
        return self._convert(html_content, strip_links=True)

    def _convert(self, html_content: str, strip_links: bool) -> str:
        """
        Método interno de conversión.

        Args:
            html_content: Contenido HTML a convertir
            strip_links: Si True, remueve links (<a> tags) preservando texto

        Returns:
            Contenido en formato Markdown

        Raises:
            ValueError: Si el contenido está vacío o la conversión falla
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")

        try:
            # Configurar tags a remover
            strip_tags = ["script", "style"]
            if strip_links:
                strip_tags.append("a")  # Remover links pero preservar texto

            markdown_content = md(
                html_content,
                heading_style="ATX",
                bullets="-",
                strong_em_symbol="**",
                strip=strip_tags,
                escape_asterisks=False,
                escape_underscores=False,
            )

            # Limpieza de espacios
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            markdown_content = re.sub(r" {2,}", " ", markdown_content)

            return markdown_content.strip()

        except Exception as e:
            raise ValueError(f"Failed to convert HTML to Markdown: {str(e)}") from e
