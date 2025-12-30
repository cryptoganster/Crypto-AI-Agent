"""Interface para ArticleReadabilityService - Domain Service."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article


class IArticleReadabilityService(ABC):
    """
    Interface para servicio de análisis de legibilidad de artículos.

    RESPONSABILIDAD ÚNICA: Calcular métricas de legibilidad del contenido.
    - Flesch Reading Ease score
    - Gunning Fog Index
    - Métricas de complejidad de texto
    - Estadísticas de contenido (palabras, oraciones, párrafos)
    """

    @abstractmethod
    def calculate_readability_score(self, article: Article) -> float:
        """
        Calcula el Flesch Reading Ease score del artículo.

        Args:
            article: Artículo a analizar

        Returns:
            Score entre 0.0 y 1.0 (1.0 = más legible)
        """
        pass

    @abstractmethod
    def calculate_gunning_fog_index(self, article: Article) -> Optional[float]:
        """
        Calcula el Gunning Fog Index (nivel de educación requerido).

        Args:
            article: Artículo a analizar

        Returns:
            Índice Gunning Fog (años de educación necesarios)
        """
        pass

    @abstractmethod
    def get_content_statistics(self, article: Article) -> Dict[str, int]:
        """
        Obtiene estadísticas básicas del contenido.

        Args:
            article: Artículo a analizar

        Returns:
            Dict con estadísticas: word_count, sentence_count, paragraph_count, etc.
        """
        pass

    @abstractmethod
    def analyze_complexity(self, article: Article) -> Dict[str, float]:
        """
        Análisis completo de complejidad del texto.

        Args:
            article: Artículo a analizar

        Returns:
            Dict con métricas de complejidad: readability_score, fog_index,
            avg_word_length, avg_sentence_length, complexity_rating
        """
        pass
