"""Domain Service para cálculo de métricas de artículos RSS."""

import re
from typing import Tuple

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.metrics_calculation import (
    IArticleMetricsCalculationService,
)


class ArticleMetricsCalculationService(IArticleMetricsCalculationService):
    """
    Domain Service para calcular métricas de contenido de artículos.

    Responsabilidades:
    - Calcular word_count (contador de palabras)
    - Calcular reading_time_minutes (tiempo de lectura estimado)
    - Aplicar algoritmos de estimación de lectura

    PURE DOMAIN SERVICE: Sin dependencias externas, solo lógica de negocio.
    """

    # Velocidad promedio de lectura: 200-250 palabras por minuto
    AVERAGE_READING_SPEED_WPM = 225

    def calculate_word_count(self, article: Article) -> int:
        """
        Calcula el número de palabras en el contenido markdown del artículo.

        Args:
            article: Artículo a analizar

        Returns:
            Número de palabras en el contenido
        """
        if not article.content.markdown:
            return 0

        # content_vo.markdown ya está limpio, no necesita strip HTML
        # Dividir por espacios y filtrar elementos vacíos
        words = [word for word in article.content.markdown.split() if word.strip()]

        return len(words)

    def calculate_reading_time(self, word_count: int) -> int:
        """
        Calcula el tiempo estimado de lectura en minutos.

        Args:
            word_count: Número de palabras del contenido

        Returns:
            Tiempo de lectura en minutos (mínimo 1)
        """
        if word_count == 0:
            return 0

        # Calcular minutos basado en velocidad promedio
        minutes = word_count / self.AVERAGE_READING_SPEED_WPM

        # Redondear hacia arriba, mínimo 1 minuto
        return max(1, round(minutes))

    def calculate_metrics(self, article: Article) -> Tuple[int, int]:
        """
        Calcula ambas métricas de una vez usando content_markdown.

        Args:
            article: Artículo a analizar (requiere content_markdown)

        Returns:
            Tupla (word_count, reading_time_minutes)
        """
        word_count = self.calculate_word_count(article)
        reading_time = self.calculate_reading_time(word_count)

        return (word_count, reading_time)

    def _strip_html_tags(self, html_content: str) -> str:
        """
        Elimina tags HTML para conteo preciso de palabras.

        Args:
            html_content: Contenido HTML

        Returns:
            Texto plano sin tags HTML
        """
        # Remover tags HTML con regex
        text = re.sub(r"<[^>]+>", "", html_content)

        # Decodificar entidades HTML comunes
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Limpiar espacios múltiples
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def calculate_metrics_from_text(self, plaintext: str) -> Tuple[int, int]:
        """
        Calcula métricas desde texto plano directamente.

        Event-Driven Architecture:
        - Permite calcular métricas sin necesidad del aggregate completo
        - Usado cuando el plaintext viene del evento anterior

        Args:
            plaintext: Texto plano a analizar

        Returns:
            Tupla (word_count, reading_time_minutes)

        Raises:
            ValueError: Si el texto está vacío
        """
        if not plaintext or not plaintext.strip():
            raise ValueError("Plaintext cannot be empty")

        # Calcular word count
        words = [word for word in plaintext.split() if word.strip()]
        word_count = len(words)

        # Calcular reading time
        reading_time = self.calculate_reading_time(word_count)

        return (word_count, reading_time)
