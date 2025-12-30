"""Service: Validación centralizada para RSS Sources."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.services.validation import (
    ISourceValidationService,
)
from src.rss.feed.domain.interfaces.services.validation import (
    ValidationResult as IValidationResult,
)
from src.rss.feed.domain.value_objects import ArticleFilterCriteria
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId, SourceId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl, SourceUrl


@dataclass(frozen=True)
class ValidationResult(IValidationResult):
    """Resultado de validación con detalles específicos."""

    is_valid: bool
    errors: List[str]
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @classmethod
    def success(
        cls,
        warnings: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Crea resultado exitoso."""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            recommendations=recommendations or [],
        )

    @classmethod
    def failure(
        cls,
        errors: List[str],
        warnings: Optional[List[str]] = None,
    ) -> "ValidationResult":
        """Crea resultado con errores."""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            recommendations=[],
        )

    def add_warning(self, warning: str) -> "ValidationResult":
        """Añade warning al resultado."""
        return ValidationResult(
            is_valid=self.is_valid,
            errors=self.errors,
            warnings=self.warnings + [warning],
            recommendations=self.recommendations,
        )

    def add_recommendation(self, recommendation: str) -> "ValidationResult":
        """Añade recomendación al resultado."""
        return ValidationResult(
            is_valid=self.is_valid,
            errors=self.errors,
            warnings=self.warnings,
            recommendations=self.recommendations + [recommendation],
        )


class SourceValidationService(ISourceValidationService):
    """
    Servicio de dominio para validación de RSS Sources.

    Responsabilidades:
    - Validar Value Objects RSS (SourceName, SourceUrl)
    - Validar entidades Source completas
    - Proveer recomendaciones específicas para RSS
    - Validar criterios de filtrado de artículos RSS
    """

    def __init__(self):
        pass

    def validate_source_creation(
        self,
        name: str,
        url: str,
        source_id: Optional[RssFeedId] = None,
    ) -> ValidationResult:
        """Validación completa para creación de fuente RSS."""
        errors = []
        warnings = []
        recommendations = []

        # 1. Validar creación de SourceName
        try:
            source_name = SourceName(name)
            if len(source_name.value) < 3:
                warnings.append(
                    "Source name is very short, consider a more descriptive name"
                )
        except ValueError as e:
            errors.append(f"Invalid source name: {str(e)}")

        # 2. Validar creación de SourceUrl
        try:
            source_url = SourceUrl(url)

            # Verificar que sea una URL RSS válida
            if not self._is_rss_like_url(source_url.value):
                warnings.append(
                    "URL doesn't contain typical RSS indicators (rss, feed, xml, atom)"
                )

            # Verificar dominio local
            if self._is_local_url(source_url.value):
                warnings.append("Local URLs may not be accessible in production")

        except ValueError as e:
            errors.append(f"Invalid Source URL: {str(e)}")

        # 3. Validar SourceId si se proporciona
        if source_id:
            try:
                # El Value Object ya valida internamente
                source_id_str = str(source_id.value)
                if not source_id_str:
                    errors.append("Source ID cannot be empty")
            except Exception as e:
                errors.append(f"Invalid source ID: {str(e)}")

        # 4. Recomendaciones específicas para RSS
        recommendations.extend(
            [
                "Test the RSS feed accessibility before finalizing the source",
                "Consider configuring automatic article categorization",
                "Set up appropriate scraping intervals based on source update frequency",
                "Enable deduplication to avoid duplicate articles",
            ]
        )

        if errors:
            result = ValidationResult.failure(errors, warnings)
        else:
            result = ValidationResult.success(warnings, recommendations)

        return result

    def validate_source_entity(self, source: Source) -> ValidationResult:
        """Validación de entidad Source completa."""
        errors = []
        warnings = []
        recommendations = []

        # Validar estado interno de la entidad
        try:
            # Verificar que la fuente tenga datos válidos
            if not source.url:
                errors.append("RSS source must have a valid URL")

            if not source.name:
                errors.append("RSS source must have a valid name")

            # Validar configuración usando el aggregate Source
            if source.configuration:
                config_validation = self._validate_source_configuration(
                    source.configuration
                )
                errors.extend(config_validation.get("errors", []))
                warnings.extend(config_validation.get("warnings", []))

            # Validar métricas usando el aggregate Source
            if source.metrics:
                metrics_validation = self._validate_source_metrics(source.metrics)
                warnings.extend(metrics_validation.get("warnings", []))

        except Exception as e:
            errors.append(f"Error validating RSS source entity: {str(e)}")

        # Recomendaciones específicas basadas en el estado de la entidad
        if source.status.is_inactive():
            recommendations.append(
                "Consider activating the source to start scraping articles"
            )

        if source.status.is_suspended():
            recommendations.append(
                "Source is suspended. Check for errors and resolve issues before reactivating"
            )

        if errors:
            return ValidationResult.failure(errors, warnings)

        return ValidationResult.success(warnings, recommendations)

    def validate_article_filter_criteria(
        self, criteria: ArticleFilterCriteria
    ) -> ValidationResult:
        """Valida criterios de filtrado de artículos RSS."""
        errors = []
        warnings = []
        recommendations = []

        # Validar coherencia de criterios de calidad
        if criteria.max_quality and criteria.min_quality:
            if criteria.max_quality.value < criteria.min_quality.value:
                errors.append("Maximum quality cannot be lower than minimum quality")

        # Validar coherencia de longitud
        if criteria.max_length and criteria.min_length:
            if criteria.max_length < criteria.min_length:
                errors.append("Maximum length cannot be lower than minimum length")

        # Advertencias sobre criterios muy restrictivos
        if criteria.min_length and criteria.min_length > 1000:
            warnings.append("Very high minimum length may filter out most RSS articles")

        if criteria.max_length and criteria.max_length < 50:
            warnings.append("Very low maximum length may filter out quality content")

        # Recomendaciones
        if criteria.is_permissive():
            recommendations.append(
                "Consider adding basic quality filters for better content curation"
            )

        if not criteria.has_category_filters() and not criteria.has_tag_filters():
            recommendations.append(
                "Consider adding category or tag filters for more targeted content"
            )

        if errors:
            return ValidationResult.failure(errors, warnings)

        return ValidationResult.success(warnings, recommendations)

    def _is_rss_like_url(self, url: str) -> bool:
        """Verifica si la URL parece ser de un RSS feed."""
        url_lower = url.lower()
        rss_indicators = [
            "/rss",
            "/feed",
            ".rss",
            ".xml",
            "/atom",
            "rss.",
            "feed.",
            "feeds.",
            "/rss.xml",
            "/feed.xml",
            "/atom.xml",
        ]
        return any(indicator in url_lower for indicator in rss_indicators)

    def _is_local_url(self, url: str) -> bool:
        """Verifica si la URL es local."""
        return any(
            domain in url.lower() for domain in ["localhost", "127.0.0.1", "0.0.0.0"]
        )

    def _validate_source_configuration(
        self, configuration: Any
    ) -> Dict[str, List[str]]:
        """Valida configuración de fuente RSS (método placeholder)."""
        # Implementación básica - puede extenderse según configuración específica
        result = {"errors": [], "warnings": []}

        try:
            # Validaciones básicas de configuración
            if hasattr(configuration, "scraping_interval"):
                if (
                    configuration.scraping_interval
                    and configuration.scraping_interval < 60
                ):
                    result["warnings"].append(
                        "Very short scraping interval may overload the RSS source"
                    )

            if hasattr(configuration, "timeout"):
                if configuration.timeout and configuration.timeout > 300:
                    result["warnings"].append(
                        "Very long timeout may cause slow scraping operations"
                    )

        except Exception as e:
            result["errors"].append(f"Error validating configuration: {str(e)}")

        return result

    def _validate_source_metrics(self, metrics: Any) -> Dict[str, List[str]]:
        """Valida métricas de fuente RSS (método placeholder)."""
        # Implementación básica - puede extenderse según métricas específicas
        result = {"warnings": []}

        try:
            # Validaciones básicas de métricas
            if hasattr(metrics, "success_rate"):
                if metrics.success_rate and metrics.success_rate < 0.5:
                    result["warnings"].append(
                        "Low success rate indicates potential issues with RSS source"
                    )

            if hasattr(metrics, "error_count"):
                if metrics.error_count and metrics.error_count > 10:
                    result["warnings"].append(
                        "High error count may indicate problematic RSS source"
                    )

        except Exception:
            # No agregar warnings por errores en validación de métricas
            pass

        return result

    def validate_url_format(self, url: str) -> ValidationResult:
        """Valida formato de URL RSS usando Value Objects."""
        errors = []
        warnings = []

        if not url:
            errors.append("URL cannot be empty")
            return ValidationResult.failure(errors)

        try:
            source_url = SourceUrl(url)

            # Preferir HTTPS
            if source_url.value.startswith("http://"):
                warnings.append("Consider using HTTPS for better security")

            # Verificar que sea RSS-like
            if not self._is_rss_like_url(source_url.value):
                warnings.append(
                    "URL doesn't appear to be an RSS feed. "
                    "Ensure it points to an RSS/Atom feed."
                )

            # Verificar dominio local
            if self._is_local_url(source_url.value):
                warnings.append("Local URLs may not be accessible in production")

        except ValueError as e:
            errors.append(f"Invalid URL format: {str(e)}")

        if errors:
            return ValidationResult.failure(errors, warnings)

        return ValidationResult.success(warnings)

    def validate_batch_sources(
        self, sources_data: List[Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """Valida múltiples fuentes RSS en lote."""
        results = {}

        for i, source_data in enumerate(sources_data):
            try:
                name = source_data.get("name", "")
                url = source_data.get("url", "")
                source_id = source_data.get("source_id")

                # Usar método actualizado
                result = self.validate_source_creation(name, url, source_id)
                results[f"source_{i}"] = result

            except Exception as e:
                error_msg = f"Validation setup error: {str(e)}"
                results[f"source_{i}"] = ValidationResult.failure([error_msg])

        return results

    def get_validation_summary(
        self, results: Dict[str, ValidationResult]
    ) -> Dict[str, int]:
        """Genera resumen de validación para múltiples resultados."""
        summary = {
            "total_sources": len(results),
            "valid_sources": sum(1 for r in results.values() if r.is_valid),
            "invalid_sources": sum(1 for r in results.values() if not r.is_valid),
            "total_warnings": sum(len(r.warnings) for r in results.values()),
            "total_recommendations": sum(
                len(r.recommendations) for r in results.values()
            ),
        }

        return summary
