"""HTML to Plaintext converter usando BeautifulSoup - Article Bounded Context."""

import re

from bs4 import BeautifulSoup

from src.rss.article.domain.interfaces.external import IHtmlToPlaintextConverter


class HtmlToPlaintextConverter(IHtmlToPlaintextConverter):
    """
    Converter de HTML a texto plano usando BeautifulSoup + lxml.

    IDEAL PARA NLP:
    - Detección de idioma (fastText)
    - Extracción de keywords
    - Análisis de sentimiento
    """

    def convert(self, html_content: str) -> str:
        """Convierte HTML a texto plano limpio."""
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")

        soup = BeautifulSoup(html_content, "lxml")

        # Remover elementos no deseados
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "figure",
                "img",
                "form",
                "input",
                "button",
                "iframe",
                "svg",
            ]
        ):
            tag.decompose()

        plaintext = soup.get_text(separator=" ", strip=True)
        plaintext = re.sub(r"\s+", " ", plaintext)

        return plaintext.strip()
