"""Interface para ArticleMetricsCalculationService."""

from typing import Protocol, Tuple

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article


class IArticleMetricsCalculationService(Protocol):
    """
    Interface para servicio de cálculo de métricas de artículos.

    Dependency Inversion Principle: Application layer depende de esta abstracción.
    """

    # Velocidad promedio de lectura: 200-250 palabras por minuto
    AVERAGE_READING_SPEED_WPM: int = 225

    def calculate_word_count(self, article: Article) -> int:
        """
        Calcula el número de palabras en el contenido del artículo.

        Args:
            article: Artículo a analizar

        Returns:
            Número de palabras en el contenido
        """
        ...

    def calculate_reading_time(self, word_count: int) -> int:
        """
        Calcula el tiempo estimado de lectura en minutos.

        Args:
            word_count: Número de palabras del contenido

        Returns:
            Tiempo de lectura en minutos (mínimo 1)
        """
        ...

    def calculate_metrics(self, article: Article) -> Tuple[int, int]:
        """
        Calcula ambas métricas de una vez.

        Args:
            article: Artículo a analizar

        Returns:
            Tupla (word_count, reading_time_minutes)
        """
        ...

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
        ...
