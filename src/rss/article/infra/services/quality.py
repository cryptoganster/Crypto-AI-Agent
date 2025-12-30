"""Implementación de ArticleQualityService en Infrastructure Layer."""

from typing import Optional

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.services.readability import (
    IArticleReadabilityService,
)
from src.rss.article.domain.value_objects import (
    Level,
    LevelEnum,
)
from src.shared.domain.value_objects import QualityThreshold


class ArticleQualityService:
    """
    Implementación de servicio de evaluación de calidad en Infrastructure Layer.

    Responsabilidades:
    - Evaluar calidad general del artículo
    - Combinar múltiples métricas (legibilidad, longitud, estructura, metadatos)
    - Retornar Level basado en evaluación

    IMPORTANTE: Este servicio IMPORTA el Article aggregate (correcto según Clean Architecture).
    El aggregate NO debe importar este servicio.
    """

    def __init__(
        self,
        readability_service: Optional[IArticleReadabilityService] = None,
        quality_threshold: Optional[QualityThreshold] = None,
    ):
        """
        Inicializa el servicio de calidad.

        Args:
            readability_service: Servicio de legibilidad (opcional)
            quality_threshold: Threshold de calidad mínima (opcional, default: medium)
        """
        self._readability_service = readability_service
        self._quality_threshold = quality_threshold or QualityThreshold.medium()

    def assess_quality(self, article: Article) -> Level:
        """
        Evalúa y retorna nivel de calidad del artículo.

        Combina múltiples métricas para determinar el nivel de calidad:
        - Legibilidad (30%)
        - Longitud del contenido (25%)
        - Completitud de metadatos (20%)
        - Calidad del título (15%)
        - Estructura del contenido (10%)

        Args:
            article: Article aggregate a evaluar

        Returns:
            Level Value Object

        Raises:
            ValueError: Si el artículo no tiene suficiente información
        """
        if not self._has_minimum_information(article):
            raise ValueError(
                "El artículo debe tener al menos título y contenido para evaluar calidad"
            )

        # Calcular score ponderado de múltiples factores
        score = 0.0
        factors = []

        # Factor 1: Legibilidad (30%)
        readability_score = self._calculate_readability_factor(article)
        factors.append(("readability", readability_score, 0.30))

        # Factor 2: Longitud del contenido (25%)
        length_score = self._calculate_length_factor(article)
        factors.append(("length", length_score, 0.25))

        # Factor 3: Completitud de metadatos (20%)
        metadata_score = self._calculate_metadata_factor(article)
        factors.append(("metadata", metadata_score, 0.20))

        # Factor 4: Calidad del título (15%)
        title_score = self._calculate_title_factor(article)
        factors.append(("title", title_score, 0.15))

        # Factor 5: Estructura del contenido (10%)
        structure_score = self._calculate_structure_factor(article)
        factors.append(("structure", structure_score, 0.10))

        # Calcular score ponderado total
        for name, factor_score, weight in factors:
            score += factor_score * weight

        # Normalizar al rango 0.0-1.0
        score = max(0.0, min(1.0, score))

        # Convertir score a Level
        return Level.from_score(score)

    def _has_minimum_information(self, article: Article) -> bool:
        """Verifica si el artículo tiene información mínima para evaluar."""
        has_title = bool(
            article.metadata.title and len(str(article.metadata.title).strip()) > 0
        )
        has_content = bool(
            (article.content.markdown and len(article.content.markdown.strip()) > 0)
            or (
                article.content.plaintext and len(article.content.plaintext.strip()) > 0
            )
        )
        return has_title and has_content

    def _calculate_readability_factor(self, article: Article) -> float:
        """Calcula factor de legibilidad (0.0-1.0)."""
        if self._readability_service:
            try:
                readability_score = (
                    self._readability_service.calculate_readability_score(article)
                )
                return readability_score
            except (ValueError, AttributeError):
                pass

        content = self._get_content_for_analysis(article)
        if not content:
            return 0.5

        words = content.split()
        if not words:
            return 0.5

        avg_word_length = sum(len(word) for word in words) / len(words)

        if avg_word_length <= 5:
            return 1.0
        elif avg_word_length <= 6:
            return 0.8
        elif avg_word_length <= 7:
            return 0.6
        elif avg_word_length <= 8:
            return 0.4
        else:
            return 0.2

    def _calculate_length_factor(self, article: Article) -> float:
        """Calcula factor de longitud del contenido (0.0-1.0)."""
        content = self._get_content_for_analysis(article)
        if not content:
            return 0.0

        word_count = len(content.split())

        if word_count < 100:
            return 0.2
        elif word_count < 300:
            return 0.5
        elif word_count < 500:
            return 0.7
        elif word_count <= 3000:
            return 1.0
        elif word_count <= 5000:
            return 0.8
        else:
            return 0.6

    def _calculate_metadata_factor(self, article: Article) -> float:
        """Calcula factor de completitud de metadatos (0.0-1.0)."""
        completeness = 0.0
        total_fields = 5

        if article.metadata.author and article.metadata.author.value:
            completeness += 1

        if article.published_at:
            completeness += 1

        if article.metadata.category and article.metadata.category.value:
            completeness += 1

        if (
            article.metadata.tags
            and article.metadata.tags.sorted_tags
            and len(article.metadata.tags.sorted_tags) > 0
        ):
            completeness += 1

        if article.metadata.summary and len(str(article.metadata.summary)) > 50:
            completeness += 1

        return completeness / total_fields

    def _calculate_title_factor(self, article: Article) -> float:
        """Calcula factor de calidad del título (0.0-1.0)."""
        if not article.metadata.title:
            return 0.0

        title = str(article.metadata.title).strip()
        title_length = len(title)

        if title_length < 10:
            return 0.3
        if title_length > 200:
            return 0.5
        if 30 <= title_length <= 100:
            return 1.0
        if 10 <= title_length < 30 or 100 < title_length <= 200:
            return 0.7

        return 0.5

    def _calculate_structure_factor(self, article: Article) -> float:
        """Calcula factor de estructura del contenido (0.0-1.0)."""
        score = 0.0

        if article.content.markdown:
            score += 0.4

        if article.content.plaintext:
            score += 0.3

        if article.content.excerpt:
            score += 0.3

        return min(1.0, score)

    def _get_content_for_analysis(self, article: Article) -> str:
        """Obtiene el mejor contenido disponible para análisis."""
        if article.content.plaintext and article.content.plaintext.strip():
            return article.content.plaintext.strip()

        if article.content.markdown and article.content.markdown.strip():
            return article.content.markdown.strip()

        return ""

    def _meets_minimum_quality_threshold(self, quality_level: Level) -> bool:
        """Verifica si un quality level cumple con el threshold mínimo configurado."""
        return quality_level.score >= self._quality_threshold.score

    def calculate_content_quality_score(self, article: Article) -> float:
        """Calcula el score de calidad del contenido (0.0-1.0)."""
        quality_level = self.assess_quality(article)
        return quality_level.score
