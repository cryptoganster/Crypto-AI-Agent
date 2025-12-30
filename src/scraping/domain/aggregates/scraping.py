"""Scraping Aggregate Root - Gestiona sesiones de scraping para fuentes RSS."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set
from uuid import uuid4

from src.rss.feed.domain.value_objects import SourceId
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.scraping.domain.entities import (
    ScrapingId,
    ScrapingManager,
    ScrapingRecord,
    ScrapingRecordStatus,
)
from src.scraping.domain.events import (
    ScrapingCompleted,
    ScrapingConfigurationUpdated,
    ScrapingFailed,
    ScrapingStarted,
)
from src.scraping.domain.value_objects import (
    ScrapingConfig,
    ScrapingError,
    ScrapingIdentity,
    ScrapingMetrics,
    ScrapingProgress,
    ScrapingState,
    ScrapingStatus,
    ScrapingTimestamps,
)
from src.shared.kernel import IAggregateRoot, IDomainEvent


class Scraping(IAggregateRoot):
    """
    Scraping Aggregate Root - Gestiona todas las operaciones de scraping para fuentes RSS.

    Este aggregate es responsable de:
    - Gestión completa del ciclo de vida de sesiones de scraping
    - Mantenimiento del historial de scraping
    - Coordinación de timing y scheduling de scraping
    - Emisión de eventos de dominio relacionados con scraping

    Separación limpia: Source maneja identidad/estado, Scraping maneja operaciones de scraping.
    """

    def __init__(
        self,
        source_id: SourceId,
        configuration: SourceConfiguration,
        scraping_id: str,
        sources_to_scrape: Optional[List[SourceId]] = None,
        config: Optional["ScrapingConfig"] = None,
    ) -> None:
        """
        Constructor simple - solo inicializa estado usando Value Objects.

        NO valida (Factory ya validó).
        NO emite eventos (Factory emite).

        Args:
            source_id: ID de la fuente RSS asociada (para compatibilidad)
            configuration: Configuración de scraping (para compatibilidad)
            scraping_id: ID único de la sesión de scraping (requerido)
            sources_to_scrape: Lista de sources a procesar (multi-source)
            config: Configuración de la sesión (multi-source)
        """
        # ✅ CORRECTO - super().__init__() primero
        super().__init__()

        # Value Objects compuestos
        self._identity = ScrapingIdentity(
            id=scraping_id,
            source_id=source_id,
            version=0,
        )

        self._timestamps = ScrapingTimestamps.create_new()

        self._progress = ScrapingProgress.create_new(
            sources=sources_to_scrape or [source_id]
        )

        self._state = ScrapingState.create_new()

        # Métricas y configuración
        self._metrics: ScrapingMetrics = ScrapingMetrics()

        if config is None:
            self._config: ScrapingConfig = ScrapingConfig()
        else:
            self._config = config

        # ScrapingManager entity para gestión interna
        self._scraping_manager: ScrapingManager = ScrapingManager(
            source_id=str(source_id), configuration=configuration
        )

        # Domain events ya inicializados por IAggregateRoot
        # (no necesitamos inicializarlos aquí)

    @property
    def id(self) -> str:
        """ID único de la sesión de scraping."""
        return self._identity.id

    @property
    def source_id(self) -> SourceId:
        """ID de la fuente RSS asociada."""
        return self._identity.source_id

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._timestamps.created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización."""
        return self._timestamps.updated_at

    @property
    def last_scraping_at(self) -> Optional[datetime]:
        """Timestamp del último scraping."""
        return self._scraping_manager.last_scraping_at

    @property
    def scraping_state(self) -> ScrapingStatus:
        """Estado actual de scraping."""
        return self._scraping_manager.scraping_state

    @property
    def can_start_scraping(self) -> bool:
        """True si se puede iniciar un nuevo scraping."""
        return self._scraping_manager.can_start_scraping

    @property
    def is_scraping_active(self) -> bool:
        """True si hay un scraping en progreso."""
        return self._scraping_manager.is_scraping_active

    @property
    def next_scraping_at(self) -> Optional[datetime]:
        """Timestamp del próximo scraping programado."""
        return self._scraping_manager.next_scraping_at

    @property
    def scraping_history(self) -> List[ScrapingRecord]:
        """Lista de registros de scraping (copia para inmutabilidad)."""
        return self._scraping_manager.scraping_history

    @property
    def version(self) -> int:
        """Versión del aggregate para optimistic locking."""
        return self._identity.version

    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Lista de eventos de dominio pendientes (solo lectura)."""
        return self._domain_events.copy()

    # Properties para multi-source support

    @property
    def sources_to_scrape(self) -> List[SourceId]:
        """Lista de sources a procesar."""
        return self._progress.sources_to_scrape.copy()

    @property
    def sources_in_progress(self) -> Set[SourceId]:
        """Set de sources actualmente en progreso."""
        return self._progress.sources_in_progress.copy()

    @property
    def sources_completed(self) -> Set[SourceId]:
        """Set de sources completados exitosamente."""
        return self._progress.sources_completed.copy()

    @property
    def sources_failed(self) -> Set[SourceId]:
        """Set de sources que fallaron."""
        return self._progress.sources_failed.copy()

    @property
    def metrics(self) -> ScrapingMetrics:
        """Métricas de la sesión."""
        return self._metrics

    @property
    def config(self) -> ScrapingConfig:
        """Configuración de la sesión."""
        return self._config

    @property
    def errors(self) -> List[ScrapingError]:
        """Lista de errores ocurridos."""
        return self._state.errors.copy()

    @property
    def cancelled_reason(self) -> Optional[str]:
        """Razón de cancelación si aplica."""
        return self._state.cancelled_reason

    @property
    def completed_at(self) -> Optional[datetime]:
        """Timestamp de completado."""
        return self._timestamps.completed_at

    @property
    def status(self) -> str:
        """
        Estado actual de la sesión derivado del progreso.

        Returns:
            Estado: 'pending', 'running', 'completed', 'failed', 'cancelled'
        """
        if self._state.is_cancelled():
            return "cancelled"

        if self._timestamps.is_completed():
            # Determinar si completó exitosamente o falló
            if len(self._progress.sources_failed) == len(
                self._progress.sources_to_fetch
            ):
                return "failed"
            return "completed"

        if len(self._progress.sources_in_progress) > 0:
            return "running"

        if (
            len(self._progress.sources_completed) > 0
            or len(self._progress.sources_failed) > 0
        ):
            return "running"  # Ya empezó pero no está completo

        return "pending"

    def start_scraping(
        self,
        scraping_type: str = "scheduled",
        timeout_seconds: int = 30,
        max_articles: Optional[int] = None,
        scraped_by: Optional[str] = None,
    ) -> ScrapingId:
        """
        Inicia una nueva operación de scraping.

        Args:
            scraping_type: Tipo de scraping (scheduled, manual, retry)
            timeout_seconds: Timeout en segundos
            max_articles: Límite máximo de artículos
            scraped_by: Usuario o sistema que inicia el scraping

        Returns:
            ID del registro de scraping creado

        Raises:
            ValueError: Si no se puede iniciar el scraping
        """
        # Delegar validación y creación al ScrapingManager
        scraping_id = self._scraping_manager.start_scraping(
            scraping_type=scraping_type,
            timeout_seconds=timeout_seconds,
            max_articles=max_articles,
            scraped_by=scraped_by,
        )

        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento de inicio de scraping
        self._add_domain_event(
            ScrapingStarted(
                aggregate_id=str(self._identity.id),
                source_id=str(self._identity.source_id),
                scraping_id=str(self._identity.id),
                sources_count=1,  # Una fuente por operación
                max_concurrent=1,
                timeout_seconds=timeout_seconds,
                started_at=self._updated_at,
            )
        )

        return scraping_id

    def complete_scraping(
        self,
        scraping_id: ScrapingId,
        articles_found: int,
        articles_new: int = 0,
        response_time_ms: Optional[float] = None,
        bytes_processed: Optional[int] = None,
        http_status_code: Optional[int] = None,
    ) -> None:
        """
        Completa una operación de scraping exitosamente.

        Args:
            scraping_id: ID del scraping a completar
            articles_found: Total de artículos encontrados
            articles_new: Artículos nuevos
            response_time_ms: Tiempo de respuesta
            bytes_processed: Bytes procesados
            http_status_code: Código de estado HTTP

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no permite completar el scraping
        """
        # Delegar al ScrapingManager
        duration_ms = self._scraping_manager.complete_scraping(
            scraping_id=scraping_id,
            articles_found=articles_found,
            articles_new=articles_new,
            response_time_ms=response_time_ms,
            bytes_processed=bytes_processed,
            http_status_code=http_status_code,
        )

        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento de scraping completado
        self._add_domain_event(
            ScrapingCompleted(
                aggregate_id=str(self._identity.id),
                source_id=(
                    str(self._identity.source_id)
                    if self._identity.source_id
                    else "unknown"
                ),
                scraping_id=str(self._identity.id),
                final_status="completed",
                articles_scraped=articles_found,
                sources_processed=1,
                sources_successful=1 if articles_found > 0 else 0,
                duration_seconds=int(duration_ms / 1000) if duration_ms else 0,
                completed_at=self._updated_at,
            )
        )

    def fail_scraping(
        self,
        scraping_id: ScrapingId,
        error_message: str,
        http_status_code: Optional[int] = None,
    ) -> tuple[float, bool]:
        """
        Marca una operación de scraping como fallida.

        Args:
            scraping_id: ID del scraping que falló
            error_message: Mensaje de error
            http_status_code: Código de estado HTTP si aplica

        Returns:
            Tuple con (duration_ms, should_suspend_source)

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no permite fallar el scraping
        """
        # Delegar al ScrapingManager
        duration_ms, should_suspend = self._scraping_manager.fail_scraping(
            scraping_id=scraping_id,
            error_message=error_message,
            http_status_code=http_status_code,
        )

        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento de scraping fallido
        self._add_domain_event(
            ScrapingFailed(
                source_id=(
                    str(self._identity.source_id)
                    if self._identity.source_id
                    else "unknown"
                ),
                scraping_id=str(self._identity.id),
                failed_sources=[],
                error_type="SCRAPING_ERROR",
                error_message=error_message,
                sources_attempted=1,
                sources_failed=1,
                failed_at=self._updated_at,
            )
        )

        return duration_ms, should_suspend

    def cancel_scraping(
        self, scraping_id: ScrapingId, reason: str = "Cancelado por usuario"
    ) -> None:
        """
        Cancela una operación de scraping en progreso.

        Args:
            scraping_id: ID del scraping a cancelar
            reason: Razón de cancelación

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el scraping no puede ser cancelado
        """
        # Delegar al ScrapingManager
        duration_ms = self._scraping_manager.cancel_scraping(
            scraping_id=scraping_id, reason=reason
        )

        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento de scraping fallido por cancelación
        self._add_domain_event(
            ScrapingFailed(
                source_id=str(self._identity.source_id),
                scraping_id=str(self._identity.id),
                failed_sources=[str(self._identity.source_id)],
                error_type="CANCELLED",
                error_message=reason,
                sources_attempted=1,
                sources_failed=1,
                failed_at=self._updated_at,
            )
        )

    def timeout_scraping(self, scraping_id: ScrapingId) -> None:
        """
        Marca un scraping como terminado por timeout.

        Args:
            scraping_id: ID del scraping que hizo timeout

        Raises:
            KeyError: Si el scraping_id no existe
            ValueError: Si el estado no es consistente
        """
        # Delegar al ScrapingManager
        duration_ms = self._scraping_manager.timeout_scraping(scraping_id)

        self._updated_at = datetime.now(timezone.utc)

        # Emitir evento de scraping fallido por timeout
        error_msg = f"Scraping timeout después de {duration_ms}ms"
        self._add_domain_event(
            ScrapingFailed(
                source_id=str(self._identity.source_id),
                scraping_id=str(self._identity.id),
                failed_sources=[str(self._identity.source_id)],
                error_type="TIMEOUT",
                error_message=error_msg,
                sources_attempted=1,
                sources_failed=1,
                failed_at=self._updated_at,
            )
        )

    def update_configuration(
        self, new_config: SourceConfiguration, reason: Optional[str] = None
    ) -> None:
        """Actualiza la configuración de scraping para esta operación específica."""
        if new_config != self._scraping_manager._configuration:
            previous_config = self._scraping_manager._configuration
            self._scraping_manager.update_configuration(new_config)
            self._updated_at = datetime.now(timezone.utc)

            # Emitir evento de configuración actualizada
            self._add_domain_event(
                ScrapingConfigurationUpdated(
                    scraping_id=str(self._identity.id),
                    source_id=str(self._identity.source_id),
                    updated_fields=["configuration"],
                    previous_config=previous_config,
                    new_config=new_config,
                    updated_at=self._updated_at,
                    updated_by="system",
                )
            )

    def is_ready_for_scraping(self, is_source_active: bool = True) -> bool:
        """
        Verifica si está lista para ser scrapeada.

        Args:
            is_source_active: True si la fuente está activa

        Returns:
            True si está lista para hacer scraping
        """
        return self._scraping_manager.is_ready_for_scraping(
            is_source_active=is_source_active
        )

    def get_recent_scraping_history(self, limit: int = 10) -> List[ScrapingRecord]:
        """
        Obtiene el historial de scraping reciente.

        Args:
            limit: Número máximo de registros

        Returns:
            Lista de registros ordenados por fecha (más recientes primero)
        """
        return self._scraping_manager.get_recent_scraping_history(limit=limit)

    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de scraping del manager interno."""
        return self._scraping_manager.get_scraping_statistics()

    def schedule_next_scraping(self, is_source_active: bool) -> None:
        """Programa próximo scraping basado en estado de la fuente."""
        self._scraping_manager.schedule_next_scraping(is_source_active=is_source_active)

    # Métodos para tracking multi-source

    def start_source_scrape(self, source_id: SourceId) -> None:
        """
        Marca un source como en progreso.

        Args:
            source_id: ID del source que inicia scraping

        Raises:
            ValueError: Si el source no está en la lista o ya está en progreso
        """
        # Delegar validación y cambio al VO
        self._progress = self._progress.start_source(source_id)
        self._timestamps = self._timestamps.with_updated()

    def complete_source_scrape(
        self,
        source_id: SourceId,
        articles_discovered: int = 0,
        articles_new: int = 0,
        articles_updated: int = 0,
        processing_time_seconds: float = 0.0,
        response_time_ms: float = 0.0,
    ) -> None:
        """
        Marca un source como completado exitosamente.

        Args:
            source_id: ID del source completado
            articles_discovered: Total de artículos descubiertos
            articles_new: Artículos nuevos
            articles_updated: Artículos actualizados
            processing_time_seconds: Tiempo de procesamiento
            response_time_ms: Tiempo de respuesta

        Raises:
            ValueError: Si el source no está en progreso
        """
        # Delegar cambio de progreso al VO
        self._progress = self._progress.complete_source(source_id)

        # Actualizar métricas
        self._metrics = ScrapingMetrics(
            articles_discovered=self._metrics.articles_discovered + articles_discovered,
            articles_new=self._metrics.articles_new + articles_new,
            articles_updated=self._metrics.articles_updated + articles_updated,
            sources_successful=self._metrics.sources_successful + 1,
            sources_failed=self._metrics.sources_failed,
            total_processing_time_seconds=self._metrics.total_processing_time_seconds
            + processing_time_seconds,
            average_response_time_ms=(
                (
                    self._metrics.average_response_time_ms
                    * self._metrics.sources_successful
                    + response_time_ms
                )
                / (self._metrics.sources_successful + 1)
                if self._metrics.sources_successful > 0
                else response_time_ms
            ),
        )

        self._timestamps = self._timestamps.with_updated()

        # Verificar si la sesión está completa
        if self._progress.is_complete():
            self._complete_session()

    def fail_source_scrape(
        self,
        source_id: SourceId,
        error_type: str,
        error_message: str,
        is_recoverable: bool = True,
        http_status_code: Optional[int] = None,
    ) -> None:
        """
        Marca un source como fallido.

        Args:
            source_id: ID del source que falló
            error_type: Tipo de error
            error_message: Mensaje de error
            is_recoverable: Si el error es recuperable
            http_status_code: Código HTTP si aplica

        Raises:
            ValueError: Si el source no está en progreso
        """
        # Delegar cambio de progreso al VO
        self._progress = self._progress.fail_source(source_id)

        # Registrar error en state VO
        error = ScrapingError(
            source_id=source_id,
            error_type=error_type,
            error_message=error_message,
            occurred_at=datetime.now(timezone.utc),
            is_recoverable=is_recoverable,
            http_status_code=http_status_code,
        )
        self._state = self._state.with_error(error)

        # Actualizar métricas
        self._metrics = ScrapingMetrics(
            articles_discovered=self._metrics.articles_discovered,
            articles_new=self._metrics.articles_new,
            articles_updated=self._metrics.articles_updated,
            sources_successful=self._metrics.sources_successful,
            sources_failed=self._metrics.sources_failed + 1,
            total_processing_time_seconds=self._metrics.total_processing_time_seconds,
            average_response_time_ms=self._metrics.average_response_time_ms,
        )

        self._timestamps = self._timestamps.with_updated()

        # Verificar si la sesión está completa
        if self._progress.is_complete():
            self._complete_session()

    def cancel_session(self, reason: str) -> None:
        """
        Cancela la sesión de scraping.

        Args:
            reason: Razón de cancelación

        Raises:
            ValueError: Si la sesión ya está completada
        """
        if self._timestamps.is_completed():
            raise ValueError("No se puede cancelar una sesión ya completada")

        # Marcar como cancelada en state VO
        self._state = self._state.with_cancellation(reason)

        # Mover todos los sources en progreso a failed
        for source_id in list(self._progress.sources_in_progress):
            self.fail_source_scrape(
                source_id=source_id,
                error_type="CANCELLED",
                error_message=reason,
                is_recoverable=False,
            )

        # Completar la sesión
        self._complete_session()

        # Emitir evento de scraping fallido
        self._add_domain_event(
            ScrapingFailed(
                source_id=str(self._identity.source_id),
                scraping_id=str(self._identity.id),
                failed_sources=[str(sid) for sid in self._progress.sources_failed],
                error_type="CANCELLED",
                error_message=reason,
                sources_attempted=len(self._progress.sources_to_scrape),
                sources_failed=len(self._progress.sources_failed),
                failed_at=self._timestamps.updated_at,
            )
        )

    # Métodos de query

    def calculate_progress_percentage(self) -> float:
        """
        Calcula el porcentaje de progreso de la sesión.

        Returns:
            Porcentaje de progreso (0.0 - 100.0)
        """
        # Delegar al VO
        return self._progress.calculate_progress_percentage()

    def estimate_completion_time(self) -> Optional[datetime]:
        """
        Estima el tiempo de completado basado en el progreso actual.

        Returns:
            Timestamp estimado de completado, o None si no hay suficiente información
        """
        if self._timestamps.is_completed():
            return self._timestamps.completed_at

        processed_count = len(self._progress.sources_completed) + len(
            self._progress.sources_failed
        )
        if processed_count == 0:
            return None

        # Calcular tiempo promedio por source
        elapsed_seconds = (
            datetime.now(timezone.utc) - self._timestamps.created_at
        ).total_seconds()
        avg_seconds_per_source = elapsed_seconds / processed_count

        # Estimar tiempo restante
        remaining_sources = len(self._progress.sources_to_fetch) - processed_count
        estimated_remaining_seconds = remaining_sources * avg_seconds_per_source

        # Calcular timestamp estimado
        from datetime import timedelta

        estimated_completion = datetime.now(timezone.utc) + timedelta(
            seconds=estimated_remaining_seconds
        )

        return estimated_completion

    def is_complete(self) -> bool:
        """
        Verifica si la sesión está completa.

        Returns:
            True si todos los sources fueron procesados
        """
        # Delegar al VO
        return self._progress.is_complete()

    def get_errors_by_type(self) -> Dict[str, List[ScrapingError]]:
        """
        Agrupa errores por tipo.

        Returns:
            Diccionario con errores agrupados por tipo
        """
        # Delegar al VO
        return self._state.get_errors_by_type()

    # Event management methods ya están implementados en IAggregateRoot
    # (domain_events property, get_uncommitted_events, mark_events_as_committed, _add_domain_event)

    def increment_version(self) -> None:
        """Incrementa la versión del agregado."""
        self._identity = self._identity.with_incremented_version()
        self._timestamps = self._timestamps.with_updated()

    def __str__(self) -> str:
        return f"Scraping(source={self._identity.source_id} - {len(self._scraping_manager.scraping_history)} operations)"

    def _is_session_complete(self) -> bool:
        """
        Verifica si la sesión está completa.

        Returns:
            True si todos los sources fueron procesados (completados o fallidos)
        """
        total_processed = len(self._sources_completed) + len(self._sources_failed)
        return total_processed == len(self._sources_to_fetch)

    def _complete_session(self) -> None:
        """
        Completa la sesión de scraping.

        Calcula métricas finales y emite evento de completado.
        """
        if self._timestamps.is_completed():
            return  # Ya está completada

        # Marcar como completada
        self._timestamps = self._timestamps.with_completed()

        # Calcular tiempo total de procesamiento
        total_duration_seconds = self._timestamps.get_duration_seconds() or 0.0

        # Determinar estado final
        if len(self._progress.sources_failed) == len(self._progress.sources_to_fetch):
            final_status = "failed"
        elif len(self._progress.sources_failed) > 0:
            final_status = "partial"
        else:
            final_status = "completed"

        # Emitir evento de scraping completado
        self._add_domain_event(
            ScrapingCompleted(
                aggregate_id=str(self._identity.id),
                source_id=str(self._identity.source_id),
                scraping_id=str(self._identity.id),
                final_status=final_status,
                articles_scraped=self._metrics.articles_discovered,
                sources_processed=len(self._progress.sources_completed)
                + len(self._progress.sources_failed),
                sources_successful=len(self._progress.sources_completed),
                duration_seconds=int(total_duration_seconds),
                completed_at=self._timestamps.completed_at,
            )
        )
