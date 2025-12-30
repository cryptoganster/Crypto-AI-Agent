"""Interface para Article Quality Service del dominio RSS."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
    from src.domain.interfaces.external.rss_fetcher_service import ArticleData

from src.shared.domain.value_objects import Level as QualityLevel
from src.shared.domain.value_objects import QualityThreshold


class IArticleQualityService(ABC):
    """
    Interface para servicio de validación de calidad de artículos RSS.

    Define el contrato para validación y evaluación de calidad de contenido
    siguiendo principios de Dependency Inversion.
    """

    @abstractmethod
    def is_article_ready_for_publication(self, article: "Article") -> bool:
        """
        Determina si un artículo está listo para publicación.

        Args:
            article: Artículo a evaluar

        Returns:
            True si está listo para publicación, False otherwise
        """
        pass

    @abstractmethod
    def validate_article_quality(
        self, article: "Article", quality_level: QualityLevel
    ) -> None:
        """
        Valida y asigna nivel de calidad a un artículo.

        Args:
            article: Artículo a validar
            quality_level: Nivel de calidad asignado
        """
        pass

    @abstractmethod
    def calculate_content_quality_score(self, article: "Article") -> float:
        """
        Calcula score de calidad basado en características del contenido.

        Args:
            article: Artículo a evaluar

        Returns:
            Score de calidad entre 0.0 y 1.0
        """
        pass

    @abstractmethod
    async def validate_article(
        self, article: "Article", quality_level: Optional[str] = None
    ) -> dict:
        """
        Valida un artículo y retorna resultados de validación.

        Args:
            article: Artículo a validar
            quality_level: Nivel de calidad esperado (opcional)

        Returns:
            Dict con resultados de validación
        """
        pass

    @abstractmethod
    async def validate_rss_article(self, article: "Article") -> dict:
        """
        Valida específicamente un artículo RSS.

        Args:
            article: Artículo RSS a validar

        Returns:
            Dict con resultados de validación RSS
        """
        pass

    @abstractmethod
    def evaluate_article_data(
        self,
        article_data: "ArticleData",
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> Tuple[float, Optional["QualityLevel"]]:
        """
        Evalúa calidad de ArticleData antes de crear aggregate.

        Método optimizado para operaciones de fetch donde solo tenemos
        ArticleData y necesitamos evaluación rápida antes de crear Article.

        Args:
            article_data: Datos del artículo desde RSS fetcher
            quality_threshold: Umbral de calidad opcional para filtrado

        Returns:
            Tuple con (score, quality_level)
            - score: Score de calidad entre 0.0 y 1.0
            - quality_level: QualityLevel si score >= threshold, None otherwise
        """
        pass

    @abstractmethod
    def meets_quality_threshold(
        self, article_data: "ArticleData", threshold: QualityThreshold
    ) -> bool:
        """
        Verifica si ArticleData cumple umbral de calidad mínimo.

        Args:
            article_data: Datos del artículo a evaluar
            threshold: Umbral de calidad configurado

        Returns:
            True si cumple el umbral, False otherwise
        """
        pass
