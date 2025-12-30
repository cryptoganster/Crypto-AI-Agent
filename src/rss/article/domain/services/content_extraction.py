"""Domain Service para extracción de summary de artículos RSS."""

import re
from typing import List, Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.content_extraction import (
    IArticleContentExtractionService,
)
from src.rss.article.domain.services.sentence_relevance_scorer import (
    SentenceRelevanceScorer,
)


class ArticleContentExtractionService(IArticleContentExtractionService):
    """
    Domain Service para extraer summary de artículos RSS.

    Responsabilidades:
    - Generar summary (resumen del artículo)
    - Aplicar heurísticas de extractive summarization con sentence scoring
    - Detectar límites de oraciones para truncado limpio

    PURE DOMAIN SERVICE: Sin dependencias externas, solo lógica de extracción.
    """

    # Configuración por defecto
    DEFAULT_SUMMARY_LENGTH = 500  # caracteres

    def __init__(self, keywords: Optional[List[str]] = None):
        """
        Inicializa el servicio de extracción.

        Args:
            keywords: Lista opcional de palabras clave para scoring de relevancia
        """
        self._sentence_scorer = SentenceRelevanceScorer(keywords=keywords)

    def generate_summary(
        self, article: Article, max_length: int = DEFAULT_SUMMARY_LENGTH
    ) -> str:
        """
        Genera un summary (resumen) del artículo usando content_markdown.

        El summary captura las oraciones más relevantes del contenido
        usando extractive summarization con sentence scoring.

        Args:
            article: Artículo del que extraer summary (requiere content_markdown)
            max_length: Longitud máxima del summary en caracteres

        Returns:
            Summary del artículo
        """
        if not article.content.markdown:
            return ""

        # content_vo.markdown ya es texto plano
        plain_text = article.content.markdown

        if len(plain_text) <= max_length:
            return plain_text

        # Dividir en oraciones
        sentences = self._split_into_sentences(plain_text)

        if not sentences:
            return self._truncate_at_sentence_boundary(plain_text, max_length)

        # ESTRATEGIA: Usar sentence scoring para seleccionar oraciones más relevantes
        scored_sentences = self._sentence_scorer.score_sentences(sentences)
        selected_sentences = self._sentence_scorer.select_top_sentences(
            scored_sentences, max_length
        )

        if not selected_sentences:
            # Si ninguna oración cabe, truncar la primera
            return self._truncate_at_sentence_boundary(sentences[0], max_length)

        return " ".join(selected_sentences)

    def _strip_html(self, html_content: str) -> str:
        """Elimina tags HTML del contenido."""
        # Remover tags HTML con regex
        text = re.sub(r"<[^>]+>", " ", html_content)

        # Decodificar entidades HTML comunes
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")

        # Normalizar espacios
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Divide texto en oraciones.

        Usa heurística simple basada en puntuación.
        """
        # Regex para detectar fin de oración
        # Busca . ! ? seguidos de espacio y mayúscula
        sentence_endings = re.compile(r"([.!?])\s+(?=[A-Z])")

        # Dividir en oraciones
        sentences = sentence_endings.split(text)

        # Reconstruir oraciones con su puntuación
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + sentences[i + 1]
            result.append(sentence.strip())

        # Agregar última oración si existe
        if len(sentences) % 2 == 1:
            result.append(sentences[-1].strip())

        return [s for s in result if s]

    def _truncate_at_sentence_boundary(self, text: str, max_length: int) -> str:
        """
        Trunca texto en límite de oración para mejor legibilidad.

        Args:
            text: Texto a truncar
            max_length: Longitud máxima

        Returns:
            Texto truncado en límite de oración
        """
        if len(text) <= max_length:
            return text

        # Buscar último límite de oración antes de max_length
        truncated = text[:max_length]

        # Buscar último . ! ? dentro del límite
        last_period = max(
            truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?")
        )

        if last_period > max_length * 0.5:  # Al menos 50% del max_length
            return text[: last_period + 1].strip()

        # Si no hay buen límite de oración, truncar en espacio
        last_space = truncated.rfind(" ")
        if last_space > 0:
            return text[:last_space].strip()

        # Último recurso: truncar directamente
        return truncated.strip()
