"""Source Aggregate Root - Gestiona fuentes RSS individuales con fetch history."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from src.rss.feed.domain.events import (
    SourceActivated,
    SourceConfigurationUpdated,
    SourceCreated,
    SourceDeactivated,
    SourceHealthDegraded,
    SourceHealthRecovered,
    SourceMetricsUpdated,
    SourceStatusChanged,
)
from src.rss.feed.domain.value_objects import (
    SourceHealth,
    SourceIdentity,
    SourceMetadata,
)
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.description import SourceDescription
from src.rss.feed.domain.value_objects.metrics import FetchData, SourceMetrics
from src.rss.feed.domain.value_objects.name import SourceName
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId, SourceId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl, SourceUrl
from src.rss.feed.domain.value_objects.status import SourceStatus
from src.scraping.domain.entities import (
    ScrapingId,
    ScrapingRecord,
    ScrapingRecordStatus,
)
from src.scraping.domain.value_objects import ScrapingStatus
from src.shared.domain.value_objects import ScrapingConfiguration, TagCollection
from src.shared.kernel import IAggregateRoot, IDomainEvent


class RssFeed(IAggregateRoot):
    """
    Source Aggregate Root - Gestiona fuentes RSS individuales.

    Este aggregate es responsable de:
    - Gestión del ciclo de vida de la fuente (activo/inactivo/suspendido)
    - Mantenimiento del historial de fetch como entidades internas
    - Emisión de eventos de dominio para coordinación con Article aggregate
    - Configuración específica de la fuente
    """

    def __init__(
        self,
        url: SourceUrl,
        name: SourceName,
        description: Optional[SourceDescription] = None,
        source_id: Optional[SourceId] = None,
        configuration: Optional[SourceConfiguration] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        scraping_config: Optional[ScrapingConfiguration] = None,
    ) -> None:
        """
        Inicializa un nuevo Source aggregate.

        Args:
            url: URL del feed RSS
            name: Nombre descriptivo de la fuente (SourceName VO)
            description: Descripción opcional (SourceDescription VO)
            source_id: ID específico (si no se proporciona, se genera)
            configuration: Configuración específica de fetch
            category: Categoría opcional de la fuente
            tags: Tags opcionales de la fuente
            scraping_config: Configuración especializada de scraping
        """
        # ✅ CORRECTO - super().__init__() primero
        super().__init__()

        # Value Objects compuestos
        now = datetime.now(timezone.utc)
        self._identity: SourceIdentity = SourceIdentity.create(
            source_id=source_id or SourceId.generate(),
            url=url,
            created_at=now,
            updated_at=now,
            version=0,
        )

        # Procesar tags
        if isinstance(tags, list):
            tags_collection = TagCollection(tags=frozenset(tags))
        elif isinstance(tags, TagCollection):
            tags_collection = tags
        else:
            tags_collection = TagCollection(tags=frozenset())

        self._metadata: SourceMetadata = SourceMetadata.create(
            name=name,
            description=description,
            category=category,
            tags=tags_collection,
            source_type="rss",
        )

        self._health: SourceHealth = SourceHealth.create_inactive()

        # Configuración
        self._configuration: SourceConfiguration = (
            configuration or SourceConfiguration()
        )
        self._scraping_config: Optional[ScrapingConfiguration] = scraping_config

    # ===== Properties para Value Objects compuestos =====

    @property
    def identity_vo(self) -> SourceIdentity:
        """SourceIdentity VO (source_id, url, created_at, updated_at, version)."""
        return self._identity

    @property
    def metadata_vo(self) -> SourceMetadata:
        """SourceMetadata VO (name, description, category, tags, source_type)."""
        return self._metadata

    @property
    def health_vo(self) -> SourceHealth:
        """SourceHealth VO (status, metrics)."""
        return self._health

    # ===== Properties delegadas a VOs compuestos =====

    @property
    def id(self) -> SourceId:
        """ID único del Source."""
        return self._identity.source_id

    @property
    def url(self) -> SourceUrl:
        """URL del feed RSS."""
        return self._identity.url

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._identity.created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización."""
        return self._identity.updated_at

    @property
    def version(self) -> int:
        """Versión del aggregate para optimistic locking."""
        return self._identity.version

    @property
    def name(self) -> SourceName:
        """Nombre de la fuente."""
        return self._metadata.name

    @property
    def description(self) -> Optional[SourceDescription]:
        """Descripción de la fuente."""
        return self._metadata.description

    @property
    def category(self) -> Optional[str]:
        """Categoría de la fuente."""
        return self._metadata.category

    @property
    def tags(self) -> TagCollection:
        """Tags de la fuente."""
        return self._metadata.tags

    @property
    def source_type(self) -> str:
        """Tipo de la fuente."""
        return self._metadata.source_type

    @property
    def status(self) -> SourceStatus:
        """Estado actual de la fuente."""
        return self._health.status

    @property
    def metrics(self) -> SourceMetrics:
        """Métricas agregadas del Source (calculadas dinámicamente)."""
        if self._health.metrics is None:
            self._calculate_metrics()
        assert self._health.metrics is not None  # Para pyright
        return self._health.metrics

    @property
    def configuration(self) -> SourceConfiguration:
        """Configuración de fetch."""
        return self._configuration

    @property
    def scraping_config(self) -> Optional[ScrapingConfiguration]:
        """Configuración especializada de scraping de la fuente."""
        return self._scraping_config

    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        """Lista de eventos de dominio pendientes (solo lectura)."""
        return self._domain_events.copy()

    @property
    def is_active(self) -> bool:
        """True si la fuente está activa."""
        return self._health.is_active()

    def is_healthy(self) -> bool:
        """True si la fuente está saludable."""
        return self._health.is_healthy()

    def activate(self) -> None:
        """
        Activa la fuente para que pueda ser fetched.

        Raises:
            ValueError: Si la fuente ya está activa o en estado error
        """
        if self._health.is_active():
            raise ValueError("La fuente ya está activa")
        if self._health.status.is_error():
            raise ValueError("No se puede activar una fuente en estado de error")

        now = datetime.now(timezone.utc)
        self._health = self._health.with_status(SourceStatus.active())
        self._identity = self._identity.with_updated_timestamp(now)

        # Emitir evento de dominio - FetchSession reaccionará automáticamente
        self._add_domain_event(
            SourceActivated(
                aggregate_id=str(self._identity.source_id),
                source_id=str(self._identity.source_id),
                activated_at=now,
            )
        )

    def deactivate(self) -> None:
        """
        Desactiva la fuente para que no sea fetched.

        Raises:
            ValueError: Si la fuente ya está inactiva
        """
        if self._health.status.is_inactive():
            raise ValueError("La fuente ya está inactiva")

        now = datetime.now(timezone.utc)
        self._health = self._health.with_status(SourceStatus.inactive())
        self._identity = self._identity.with_updated_timestamp(now)

        # Emitir evento de dominio - FetchSession reaccionará automáticamente
        self._add_domain_event(
            SourceDeactivated(
                aggregate_id=str(self._identity.source_id),
                source_id=str(self._identity.source_id),
                reason="Desactivación manual",
            )
        )

    def reset_health_metrics(self) -> None:
        """
        Resetea las métricas de salud de la fuente.

        Útil cuando se reactiva una fuente después de resolver problemas,
        o cuando se quiere dar una segunda oportunidad a una fuente con fallos.
        """
        now = datetime.now(timezone.utc)

        # Resetear métricas usando SourceHealth VO
        self._health = self._health.with_reset_metrics()
        self._identity = self._identity.with_updated_timestamp(now)

        # Emitir evento de recuperación de salud
        self._add_domain_event(
            SourceHealthRecovered(
                aggregate_id=str(self._identity.source_id),
                source_id=str(self._identity.source_id),
                recovered_at=now,
                reason="Manual health metrics reset",
            )
        )

    def suspend(self, reason: str) -> None:
        """
        Suspende la fuente por errores consecutivos.

        Args:
            reason: Razón de la suspensión
        """
        now = datetime.now(timezone.utc)
        previous_status = str(self._health.status)

        self._health = self._health.with_status(SourceStatus.suspended())
        self._identity = self._identity.with_updated_timestamp(now)

        # Emitir evento - FetchSession reaccionará para pausar fetch operations
        self._add_domain_event(
            SourceStatusChanged(
                source_id=str(self._identity.source_id),
                previous_status=previous_status,
                new_status="suspended",
                transition_reason=reason,
            )
        )

    def mark_error(self, error_message: str) -> None:
        """
        Marca la fuente en estado de error.

        Args:
            error_message: Mensaje de error
        """
        now = datetime.now(timezone.utc)
        previous_status = str(self._health.status)

        self._health = self._health.with_status(SourceStatus.error())
        self._identity = self._identity.with_updated_timestamp(now)

        # Emitir evento - FetchSession reaccionará para detener fetch operations
        self._add_domain_event(
            SourceStatusChanged(
                source_id=str(self._identity.source_id),
                previous_status=previous_status,
                new_status="error",
                transition_reason=error_message,
            )
        )

    # Métodos de fetch removidos - ahora responsabilidad del FetchSession aggregate
    # Coordinación via Application Services que manejan Source + FetchSession

    def update_configuration(self, new_config: SourceConfiguration) -> None:
        """Actualiza la configuración de la fuente."""
        if new_config != self._configuration:
            previous_config = self._configuration
            self._configuration = new_config
            self._identity = self._identity.with_updated_timestamp(
                datetime.now(timezone.utc)
            )

            # Emitir evento de configuración actualizada - FetchSession reaccionará
            self._add_domain_event(
                SourceConfigurationUpdated(
                    source_id=str(self._identity.source_id),
                    previous_config=previous_config,
                    new_config=new_config,
                )
            )

    def change_status(
        self, new_status: SourceStatus, reason: Optional[str] = None
    ) -> None:
        """Cambia el status de la fuente."""
        if new_status != self._health.status:
            previous_status = str(self._health.status)
            self._health = self._health.with_status(new_status)
            self._identity = self._identity.with_updated_timestamp(
                datetime.now(timezone.utc)
            )

            # Emitir evento de cambio de status
            self._add_domain_event(
                SourceStatusChanged(
                    source_id=str(self._identity.source_id),
                    previous_status=previous_status,
                    new_status=str(new_status),
                    transition_reason=reason,
                )
            )

    def update_details(
        self,
        name: Optional[SourceName] = None,
        description: Optional[SourceDescription] = None,
    ) -> None:
        """
        Actualiza detalles básicos de la fuente.

        Args:
            name: Nuevo nombre (SourceName VO, opcional)
            description: Nueva descripción (SourceDescription VO, opcional)
        """
        if name is not None:
            self._metadata = self._metadata.with_name(name)
        if description is not None:
            self._metadata = self._metadata.with_description(description)

        self._identity = self._identity.with_updated_timestamp(
            datetime.now(timezone.utc)
        )

    def is_ready_for_basic_operations(self) -> bool:
        """
        Verifica si la fuente está lista para operaciones básicas.

        Returns:
            True si está activa y operativa
        """
        return self._health.status.is_active() and not self._health.status.is_error()

    # Historial de fetch removido - consultar via FetchSession repository

    # Métodos de fetch eliminados: delegados al FetchSession aggregate
    # Coordinación via Application Services y Domain Events

    def update_metrics(
        self, new_metrics: SourceMetrics, has_significant_change: bool = True
    ) -> None:
        """
        Actualiza las métricas del Source y emite evento si hay cambios significativos.

        Este método es llamado por Application Services que coordinan con Domain Services.
        El agregado mantiene responsabilidad de emitir eventos de dominio.
        """
        if self._health.metrics != new_metrics:
            self._health = self._health.with_metrics(new_metrics)
            self._identity = self._identity.with_updated_timestamp(
                datetime.now(timezone.utc)
            )

            # Emitir evento si hay cambios significativos
            if has_significant_change:
                self._add_domain_event(
                    SourceMetricsUpdated(
                        source_id=str(self._identity.source_id),
                        total_fetches=new_metrics.total_fetches,
                        successful_fetches=new_metrics.successful_fetches,
                        failed_fetches=new_metrics.failed_fetches,
                        total_articles_discovered=new_metrics.total_articles_discovered,
                        total_articles_new=new_metrics.total_articles_new,
                        success_rate=new_metrics.success_rate,
                        last_fetch_at=new_metrics.last_fetch_at,
                        average_response_time_ms=new_metrics.average_response_time_ms,
                    )
                )

    def _calculate_metrics(self) -> None:
        """
        Calcula métricas básicas por defecto.

        Nota: Para cálculos reales, usar Application Services que coordinen
        con SourceMetricsCalculationService y llamen update_metrics().
        """
        # Sin historial de fetch disponible internamente, usar métricas vacías
        # Las métricas reales se calculan externamente y se actualizan via update_metrics()
        if self._health.metrics is None:
            self._health = self._health.with_metrics(SourceMetrics.empty())

    # Event management methods ya están implementados en IAggregateRoot
    # (get_uncommitted_events, mark_events_as_committed, _add_domain_event)

    def __str__(self) -> str:
        return f"Source({self._health.status.value} - {self._metadata.name} - {self._identity.url})"

    def record_health_recovered(
        self,
        *,
        source_name: str,
        source_url: str,
        recovery_health_score: float,
        recovered_at: datetime,
        downtime_duration: Optional[int],
        recovery_trigger: str,
    ) -> None:
        """Registra evento de recuperación de salud."""
        self._add_domain_event(
            SourceHealthRecovered(
                source_id=self._identity.source_id,
                source_name=source_name,
                source_url=source_url,
                previous_health_score=0.0,  # Valor por defecto
                current_health_score=recovery_health_score,
                recovery_threshold=0.7,  # Valor por defecto
                recovered_at=recovered_at,
                downtime_duration=downtime_duration,
                recovery_trigger=recovery_trigger,
            )
        )

        self._health = self._health.with_metrics(None)

    # Health events: estos métodos solo emiten eventos usando payloads
    # provistos por el Domain Service `SourceHealthService`.
    def record_health_degraded(
        self,
        source_url: str,
        previous_health_score: float,
        current_health_score: float,
        degradation_threshold: float,
        degraded_at: datetime,
        failure_count: int,
        last_successful_fetch: Optional[datetime],
        degradation_reason: str,
    ) -> None:
        """Registra evento de degradación de salud."""
        event = SourceHealthDegraded(
            source_id=self._identity.source_id,
            source_name=str(self.name),
            source_url=source_url,
            previous_health_score=previous_health_score,
            current_health_score=current_health_score,
            degradation_threshold=degradation_threshold,
            degraded_at=degraded_at,
            failure_count=failure_count,
            last_successful_fetch=last_successful_fetch,
            degradation_reason=degradation_reason,
        )
        self._add_domain_event(event)
