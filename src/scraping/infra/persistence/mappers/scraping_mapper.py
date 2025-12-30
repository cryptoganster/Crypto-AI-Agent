"""Scraping Mapper - Convierte entre Scraping aggregate y ScrapingModel."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.rss.feed.domain.value_objects import SourceId
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.value_objects import ScrapingIdentity as ScrapingId
from src.scraping.domain.value_objects import ScrapingStatus
from src.scraping.infra.persistence.models import ScrapingModel


class ScrapingMapper:
    """
    Mapper para convertir entre Scraping aggregate y ScrapingModel.

    Implementa el patrón Mapper de Infrastructure Layer,
    manteniendo separación entre domain y persistence.
    """

    @staticmethod
    def to_domain(model: ScrapingModel) -> Scraping:
        """
        Convierte ScrapingModel a Scraping aggregate (multi-source).

        Args:
            model: Modelo de persistencia

        Returns:
            Scraping aggregate reconstruido

        Raises:
            ValueError: Si los datos del modelo son inválidos
        """
        if not model:
            raise ValueError("ScrapingModel no puede ser None")

        try:
            # Importar Value Objects necesarios
            from src.scraping.domain.entities import ScrapingManager
            from src.scraping.domain.value_objects import (
                ScrapingConfig,
                ScrapingIdentity,
                ScrapingMetrics,
                ScrapingProgress,
                ScrapingState,
                ScrapingTimestamps,
            )

            # Reconstruir sources_to_fetch desde el modelo
            sources_to_fetch = [SourceId(sid) for sid in (model.sources_to_fetch or [])]

            # Crear Scraping usando __new__ para evitar __init__
            scraping = Scraping.__new__(Scraping)

            # Reconstruir Value Objects compuestos
            primary_source_id = (
                sources_to_fetch[0]
                if sources_to_fetch
                else SourceId("00000000-0000-0000-0000-000000000000")
            )

            scraping._identity = ScrapingIdentity(
                id=str(model.id),
                source_id=primary_source_id,
                version=int(model.version) if model.version else 0,
            )

            scraping._timestamps = ScrapingTimestamps(
                created_at=model.created_at,
                updated_at=model.updated_at,
                started_at=model.started_at,
                completed_at=model.completed_at,
            )

            scraping._progress = ScrapingProgress(
                sources_to_scrape=sources_to_fetch,
                sources_in_progress=set(
                    SourceId(sid) for sid in (model.sources_in_progress or [])
                ),
                sources_completed=set(
                    SourceId(sid) for sid in (model.sources_completed or [])
                ),
                sources_failed=set(
                    SourceId(sid) for sid in (model.sources_failed or [])
                ),
            )

            scraping._state = ScrapingState(
                errors=[],  # No reconstruimos errores completos
                cancelled_reason=model.cancelled_reason,
            )

            scraping._metrics = ScrapingMetrics(
                articles_discovered=model.articles_discovered or 0,
                articles_new=model.articles_new or 0,
                articles_updated=model.articles_updated or 0,
                sources_successful=model.sources_successful or 0,
                sources_failed=model.sources_failed_count or 0,
                total_processing_time_seconds=model.total_processing_time_seconds
                or 0.0,
                average_response_time_ms=model.average_response_time_ms or 0.0,
            )

            # Crear ScrapingConfig desde modelo
            scraping._config = ScrapingConfig(
                max_concurrent_scrapes=model.max_concurrent_fetches or 5,
                timeout_seconds=model.timeout_seconds or 30,
                timeout_config=model.timeout_config or {},
                retry_attempts=3,
                retry_delay_seconds=5,
                scraping_type="scheduled",
            )

            # LEGACY: Crear ScrapingManager para compatibilidad
            configuration = SourceConfiguration(
                fetch_interval_minutes=360,
                timeout_seconds=model.timeout_seconds or 30,
                custom_headers={},
            )
            scraping._fetch_manager = ScrapingManager(
                source_id=str(primary_source_id), configuration=configuration
            )

            # Inicializar eventos vacíos (no emitir eventos al reconstruir)
            scraping._domain_events = []
            scraping._uncommitted_events = []

            # Llamar super().__init__() para inicializar IAggregateRoot
            super(Scraping, scraping).__init__()

            return scraping

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo ScrapingModel a Scraping: {str(e)}"
            ) from e

    @staticmethod
    def to_model(scraping: Scraping) -> ScrapingModel:
        """
        Convierte Scraping aggregate a ScrapingModel.

        Args:
            scraping: Scraping aggregate

        Returns:
            ScrapingModel para persistencia

        Raises:
            ValueError: Si el Scraping es inválido
        """
        if not scraping:
            raise ValueError("Scraping no puede ser None")

        # DEBUG: Log para diagnosticar
        from loguru import logger

        logger.debug(
            "ScrapingMapper.to_model iniciando",
            scraping_id=str(scraping.id),
            scraping_type=type(scraping).__name__,
            has_sources_to_scrape=hasattr(scraping, "sources_to_scrape"),
            has_metrics=hasattr(scraping, "metrics"),
            has_config=hasattr(scraping, "config"),
        )

        try:
            # Convertir string ID a UUID si es necesario
            scraping_uuid = (
                UUID(scraping.id) if isinstance(scraping.id, str) else scraping.id
            )

            # Mapear sources tracking desde el aggregate
            sources_to_fetch = [str(sid) for sid in scraping.sources_to_scrape]
            sources_in_progress = [str(sid) for sid in scraping.sources_in_progress]
            sources_completed_list = [str(sid) for sid in scraping.sources_completed]
            sources_failed_list = [str(sid) for sid in scraping.sources_failed]

            # Obtener métricas desde el VO
            metrics = scraping.metrics

            # Obtener configuración desde el VO
            config = scraping.config

            # Obtener errores desde el VO
            errors = scraping.errors
            errors_by_type_dict = {
                error_type: len(error_list)
                for error_type, error_list in scraping.get_errors_by_type().items()
            }
            last_error = errors[-1] if errors else None

            # Calcular started_at (usar created_at como fallback)
            started_at = scraping.created_at

            return ScrapingModel(
                # Identity - usar 'id' (nueva convención)
                id=scraping_uuid,
                # Status
                status=scraping.status,
                cancelled_reason=scraping.cancelled_reason,
                # Configuration - desde config VO (ScrapingConfig)
                max_concurrent_fetches=config.max_concurrent_scrapes,
                timeout_seconds=config.timeout_seconds,
                timeout_config=(
                    config.timeout_config if hasattr(config, "timeout_config") else {}
                ),
                # Sources tracking - mapear desde aggregate
                sources_to_fetch=sources_to_fetch,
                sources_count=len(sources_to_fetch),
                sources_in_progress=sources_in_progress,
                sources_completed=sources_completed_list,
                sources_failed=sources_failed_list,
                # Metrics - desde metrics VO
                articles_discovered=metrics.articles_discovered,
                articles_new=metrics.articles_new,
                articles_updated=metrics.articles_updated,
                sources_successful=metrics.sources_successful,
                sources_failed_count=metrics.sources_failed,
                total_processing_time_seconds=metrics.total_processing_time_seconds,
                average_response_time_ms=metrics.average_response_time_ms,
                # Error tracking - desde state VO
                error_count=len(errors),
                errors_by_type=errors_by_type_dict,
                last_error_message=last_error.error_message if last_error else None,
                fetch_errors=[],  # No se persisten errores completos en el modelo
                # Timestamps
                started_at=started_at,
                completed_at=scraping.completed_at,
                expected_completion_at=scraping.estimate_completion_time(),
                created_at=scraping.created_at,
                updated_at=scraping.updated_at,
                version=scraping.version,
            )

        except Exception as e:
            raise ValueError(
                f"Error convirtiendo Scraping a ScrapingModel: {str(e)}"
            ) from e

    @staticmethod
    def update_model_from_domain(
        model: ScrapingModel, scraping: Scraping, logger: Optional[Any] = None
    ) -> None:
        """
        Actualiza ScrapingModel existente con datos del Scraping aggregate.

        Delega al método update_from_scraping_domain del modelo para
        asegurar que TODOS los campos se mapean correctamente.

        Args:
            model: Modelo existente a actualizar
            scraping: Scraping aggregate con datos nuevos
            logger: Logger opcional para observabilidad
        """
        if not model:
            raise ValueError("ScrapingModel no puede ser None")
        if not scraping:
            raise ValueError("Scraping no puede ser None")

        try:
            # Delegar al método del modelo que mapea TODOS los campos
            model.update_from_scraping_domain(scraping, logger=logger)

        except Exception as e:
            raise ValueError(
                f"Error actualizando ScrapingModel desde Scraping: {str(e)}"
            ) from e

    @staticmethod
    def update_model_metrics(
        model: ScrapingModel,
        articles_discovered: int = 0,
        articles_new: int = 0,
        articles_updated: int = 0,
        sources_successful: int = 0,
        sources_failed_count: int = 0,
        total_processing_time_seconds: float = 0.0,
        average_response_time_ms: float = 0.0,
        error_count: int = 0,
        errors_by_type: Optional[Dict[str, int]] = None,
        last_error_message: Optional[str] = None,
    ) -> None:
        """
        Actualiza métricas específicas del ScrapingModel.

        Método auxiliar para actualizar métricas sin afectar otros campos.

        Args:
            model: Modelo a actualizar
            articles_discovered: Total de artículos descubiertos
            articles_new: Artículos nuevos procesados
            articles_updated: Artículos actualizados
            sources_successful: Sources procesados exitosamente
            sources_failed_count: Sources que fallaron
            total_processing_time_seconds: Tiempo total de procesamiento
            average_response_time_ms: Tiempo promedio de respuesta
            error_count: Número total de errores
            errors_by_type: Conteo de errores por tipo
            last_error_message: Último mensaje de error
        """
        if not model:
            raise ValueError("ScrapingModel no puede ser None")

        try:
            # Actualizar métricas de artículos
            model.articles_discovered = articles_discovered
            model.articles_new = articles_new
            model.articles_updated = articles_updated

            # Actualizar métricas de sources
            model.sources_successful = sources_successful
            model.sources_failed_count = sources_failed_count

            # Actualizar métricas de performance
            model.total_processing_time_seconds = total_processing_time_seconds
            model.average_response_time_ms = average_response_time_ms

            # Actualizar error tracking
            model.error_count = error_count
            if errors_by_type:
                model.errors_by_type = errors_by_type
            if last_error_message:
                model.last_error_message = last_error_message

        except Exception as e:
            raise ValueError(
                f"Error actualizando métricas del ScrapingModel: {str(e)}"
            ) from e
