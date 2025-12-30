"""Interface para Source Validation Service."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.rss.feed.domain.aggregates import Source

from src.rss.feed.domain.value_objects import ArticleFilterCriteria
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId


class ValidationResult:
    """Resultado de validación con detalles específicos."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]

    @classmethod
    def success(
        cls,
        warnings: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Crea resultado exitoso."""
        ...

    @classmethod
    def failure(
        cls,
        errors: List[str],
        warnings: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Crea resultado con errores."""
        ...

    def add_warning(self, warning: str) -> "ValidationResult":
        """Añade warning al resultado."""
        ...

    def add_recommendation(self, recommendation: str) -> "ValidationResult":
        """Añade recomendación al resultado."""
        ...


class ISourceValidationService(ABC):
    """
    Interface para servicio de dominio de validación de RSS Sources.

    Responsabilidades:
    - Validar Value Objects RSS (SourceName, SourceUrl)
    - Validar entidades Source completas
    - Proveer recomendaciones específicas para RSS
    - Validar criterios de filtrado de artículos RSS
    """

    @abstractmethod
    def validate_source_creation(
        self,
        name: str,
        url: str,
        source_id: Optional[RssFeedId] = None,
    ) -> ValidationResult:
        """
        Validación completa para creación de fuente RSS.

        Args:
            name: Nombre de la source
            url: URL de la source
            source_id: ID opcional de la source

        Returns:
            ValidationResult con resultado de validación
        """
        ...

    @abstractmethod
    def validate_source_entity(self, source: "Source") -> ValidationResult:
        """
        Validación de entidad Source completa.

        Args:
            source: Source aggregate a validar

        Returns:
            ValidationResult con resultado de validación
        """
        ...

    @abstractmethod
    def validate_article_filter_criteria(
        self, criteria: ArticleFilterCriteria
    ) -> ValidationResult:
        """
        Valida criterios de filtrado de artículos RSS.

        Args:
            criteria: Criterios de filtrado a validar

        Returns:
            ValidationResult con resultado de validación
        """
        ...

    @abstractmethod
    def validate_url_format(self, url: str) -> ValidationResult:
        """
        Valida formato de URL RSS usando Value Objects.

        Args:
            url: URL a validar

        Returns:
            ValidationResult con resultado de validación
        """
        ...

    @abstractmethod
    def validate_batch_sources(
        self, sources_data: List[Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """
        Valida múltiples fuentes RSS en lote.

        Args:
            sources_data: Lista de datos de sources a validar

        Returns:
            Diccionario con resultados de validación por source
        """
        ...

    @abstractmethod
    def get_validation_summary(
        self, results: Dict[str, ValidationResult]
    ) -> Dict[str, int]:
        """
        Genera resumen de validación para múltiples resultados.

        Args:
            results: Diccionario de resultados de validación

        Returns:
            Diccionario con resumen estadístico
        """
        ...
