"""Scraping SQLAlchemy Model para Scraping aggregate.

Este modelo pertenece al bounded context Scraping y mapea el Scraping aggregate
a la tabla 'scrapings' en el schema 'crypto_news_scraper'.

Nota: Esta tabla fue renombrada de 'fetch_sessions' a 'scrapings' para
alinearse con el bounded context Scraping.

Convenciones de ID:
- id: Primary Key del aggregate (UUID)
- source_id: Referencias a Sources se almacenan en arrays (sources_to_fetch, etc.)
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.shared.infra.persistence import BaseModel
from src.shared.kernel.logger import ILogger

if TYPE_CHECKING:
    from src.scraping.domain.aggregates import Scraping
    from src.scraping.domain.interfaces.factories import IScrapingFactory


class ScrapingModel(BaseModel):
    """
    SQLAlchemy Model para Scraping aggregate.

    Mapea el Scraping aggregate a tabla de base de datos,
    optimizado para tracking de sesiones de scraping y métricas.

    Convenciones de ID:
    - id: Primary Key (UUID) - identificador único del Scraping session
    - sources_to_fetch: Array de Source IDs a procesar
    """

    __tablename__ = "scrapings"

    # === PRIMARY KEY ===
    # Convención: 'id' como PK del aggregate
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment="Scraping aggregate root ID (PK)",
    )

    # === SCRAPING SESSION CORE ===
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="Estado: pending, running, completed, failed, cancelled",
    )
    cancelled_reason = Column(
        Text,
        nullable=True,
        comment="Razón de cancelación si aplica",
    )

    # === SCRAPING CONFIG ===
    max_concurrent_fetches = Column(
        Integer,
        nullable=False,
        default=5,
        comment="Máximo fetches concurrentes permitidos",
    )
    timeout_seconds = Column(
        Integer,
        nullable=False,
        default=30,
        comment="Timeout por source en segundos",
    )
    timeout_config = Column(
        JSONB,
        default=dict,
        comment="Configuración detallada de timeouts",
    )

    # === SOURCES TRACKING ===
    sources_to_fetch = Column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Lista de source IDs a procesar",
    )
    sources_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total de sources a procesar",
    )
    sources_in_progress = Column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Source IDs actualmente en progreso",
    )
    sources_completed = Column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Source IDs completados exitosamente",
    )
    sources_failed = Column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Source IDs que fallaron",
    )

    # === SCRAPING METRICS ===
    articles_discovered = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total artículos descubiertos",
    )
    articles_new = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Artículos nuevos procesados",
    )
    articles_updated = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Artículos actualizados",
    )
    sources_successful = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Sources procesados exitosamente",
    )
    sources_failed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Sources que fallaron",
    )
    total_processing_time_seconds = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Tiempo total de procesamiento en segundos",
    )
    average_response_time_ms = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Tiempo promedio de respuesta en milisegundos",
    )

    # === ERROR TRACKING ===
    error_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Número total de errores",
    )
    errors_by_type = Column(
        JSONB,
        default=dict,
        comment="Conteo de errores por tipo",
    )
    last_error_message = Column(
        Text,
        nullable=True,
        comment="Último mensaje de error",
    )
    fetch_errors = Column(
        JSONB,
        default=list,
        comment="Lista detallada de errores de fetch",
    )

    # === SCRAPING TIMESTAMPS ===
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp de inicio de la sesión",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp de completado de la sesión",
    )
    expected_completion_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp esperado de completado",
    )

    # === PERFORMANCE INDEXES ===
    __table_args__ = (
        # Performance queries: Sesiones activas
        Index("idx_scrapings_status", "status"),
        # Performance queries: Sesiones por rango temporal
        Index("idx_scrapings_started_at", "started_at", "status"),
        # Performance queries: Sesiones completadas
        Index("idx_scrapings_completed", "completed_at", "status"),
        # Time-based indexes
        Index("idx_scrapings_created_at", "created_at"),
        Index("idx_scrapings_updated_at", "updated_at"),
        # Analytics indexes
        Index("idx_scrapings_sources_count", "sources_count"),
        Index("idx_scrapings_articles", "articles_discovered"),
        # Schema configuration
        {"schema": "crypto_news_scraper"},
    )

    def __init__(self, **kwargs):
        """Constructor con logging inyectado."""
        super().__init__(**kwargs)
        self._logger: ILogger = kwargs.get("logger")

    def to_scraping_domain(
        self,
        scraping_factory: "IScrapingFactory",
        logger: Optional[ILogger] = None,
    ) -> "Scraping":
        """
        Reconstruye el Scraping aggregate desde el modelo usando factory.

        Args:
            scraping_factory: Factory para reconstruir agregados
            logger: Logger para observabilidad

        Returns:
            Scraping: Aggregate reconstruido con TODOS los campos
        """
        if logger:
            logger.debug(
                "Reconstruyendo Scraping aggregate usando factory",
                model_id=str(self.id),
                status=self.status,
                sources_count=self.sources_count,
            )

        from src.rss.feed.domain.value_objects import SourceId
        from src.scraping.domain.value_objects import ScrapingIdentity
        from src.scraping.domain.value_objects.config import ScrapingConfig
        from src.scraping.domain.value_objects.error import ScrapingError
        from src.scraping.domain.value_objects.metrics import ScrapingMetrics

        # Reconstruir Value Objects
        scraping_id = ScrapingIdentity(self.id)

        # Reconstruir lista de sources como Value Objects
        sources_to_fetch = [SourceId(source_id) for source_id in self.sources_to_fetch]

        # Reconstruir configuración
        config = ScrapingConfig(
            max_concurrent_scrapes=self.max_concurrent_fetches,
            timeout_seconds=self.timeout_seconds,
            timeout_config=self.timeout_config or {},
        )

        # Reconstruir métricas
        metrics = ScrapingMetrics(
            articles_discovered=self.articles_discovered,
            articles_new=self.articles_new,
            articles_updated=self.articles_updated,
            sources_successful=self.sources_successful,
            sources_failed=self.sources_failed_count,
            total_processing_time_seconds=self.total_processing_time_seconds,
            average_response_time_ms=self.average_response_time_ms,
        )

        # Reconstruir errores
        errors = []
        if self.fetch_errors:
            for error_data in self.fetch_errors:
                try:
                    error = ScrapingError(
                        source_id=SourceId(error_data.get("source_id", "")),
                        error_type=error_data.get("error_type", "UNKNOWN"),
                        error_message=error_data.get("error_message", ""),
                        occurred_at=datetime.fromisoformat(
                            error_data.get(
                                "occurred_at", datetime.now(timezone.utc).isoformat()
                            )
                        ),
                        is_recoverable=error_data.get("is_recoverable", True),
                        http_status_code=error_data.get("http_status_code"),
                    )
                    errors.append(error)
                except Exception as e:
                    if logger:
                        logger.warning(
                            "Error reconstruyendo ScrapingError, omitiendo",
                            error=str(e),
                            error_data=error_data,
                        )

        # Usar factory para reconstruir aggregate
        scraping = scraping_factory.reconstruct_from_persistence(
            sources_to_fetch=sources_to_fetch,
            scraping_id=scraping_id,
            max_concurrent_fetches=self.max_concurrent_fetches,
            created_at=self.created_at,
            updated_at=self.updated_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            status=self.status,
            error_details=self.fetch_errors,
        )

        # Restaurar tracking de sources (convertir a Set)
        scraping._sources_in_progress = set(
            SourceId(sid) for sid in self.sources_in_progress
        )
        scraping._sources_completed = set(
            SourceId(sid) for sid in self.sources_completed
        )
        scraping._sources_failed = set(SourceId(sid) for sid in self.sources_failed)

        # Restaurar métricas
        scraping._metrics = metrics

        # Restaurar configuración
        scraping._config = config

        # Restaurar errores
        scraping._errors = errors

        # Restaurar razón de cancelación
        scraping._cancelled_reason = self.cancelled_reason

        # Restaurar timestamps
        scraping._completed_at = self.completed_at
        scraping._created_at = self.created_at
        scraping._updated_at = self.updated_at

        if logger:
            logger.debug(
                "Scraping aggregate reconstruido exitosamente",
                scraping_id=str(scraping.id),
                status=str(scraping.status),
                sources_count=len(scraping.sources_to_fetch),
            )

        return scraping

    def update_from_scraping_domain(
        self,
        scraping: "Scraping",
        logger: Optional[ILogger] = None,
    ) -> None:
        """
        Actualiza el modelo con cambios del Scraping aggregate.

        Args:
            scraping: Scraping aggregate actualizado
            logger: Logger para observabilidad
        """
        if logger:
            logger.debug(
                "Actualizando ScrapingModel desde Scraping aggregate",
                scraping_id=str(scraping.id),
                status=str(scraping.status),
            )

        # === ACTUALIZAR CAMPOS CORE ===
        self.status = str(scraping.status)
        self.cancelled_reason = getattr(scraping, "_cancelled_reason", None)

        # === ACTUALIZAR TRACKING DE SOURCES ===
        self.sources_to_fetch = [
            str(sid) for sid in getattr(scraping, "_sources_to_fetch", [])
        ]
        self.sources_count = len(self.sources_to_fetch)

        self.sources_in_progress = [
            str(sid) for sid in getattr(scraping, "_sources_in_progress", set())
        ]
        self.sources_completed = [
            str(sid) for sid in getattr(scraping, "_sources_completed", set())
        ]
        self.sources_failed = [
            str(sid) for sid in getattr(scraping, "_sources_failed", set())
        ]

        # === ACTUALIZAR CONFIGURACIÓN ===
        config = getattr(scraping, "_config", None)
        if config:
            self.max_concurrent_fetches = config.max_concurrent_scrapes
            self.timeout_seconds = config.timeout_seconds
            self.timeout_config = config.timeout_config or {}

        # === ACTUALIZAR MÉTRICAS ===
        metrics = getattr(scraping, "_metrics", None)
        if metrics:
            self.articles_discovered = metrics.articles_discovered
            self.articles_new = metrics.articles_new
            self.articles_updated = metrics.articles_updated
            self.sources_successful = metrics.sources_successful
            self.sources_failed_count = metrics.sources_failed
            self.total_processing_time_seconds = metrics.total_processing_time_seconds
            self.average_response_time_ms = metrics.average_response_time_ms

        # === ACTUALIZAR ERRORES ===
        errors = getattr(scraping, "_errors", [])
        if errors:
            fetch_errors_list = []
            errors_by_type_dict = {}

            for error in errors:
                error_dict = {
                    "source_id": str(error.source_id),
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "occurred_at": error.occurred_at.isoformat(),
                    "is_recoverable": error.is_recoverable,
                    "http_status_code": error.http_status_code,
                }
                fetch_errors_list.append(error_dict)

                error_type = error.error_type
                errors_by_type_dict[error_type] = (
                    errors_by_type_dict.get(error_type, 0) + 1
                )

            self.fetch_errors = fetch_errors_list
            self.error_count = len(fetch_errors_list)
            self.errors_by_type = errors_by_type_dict
            self.last_error_message = (
                fetch_errors_list[-1]["error_message"] if fetch_errors_list else None
            )
        else:
            self.fetch_errors = []
            self.error_count = 0
            self.errors_by_type = {}
            self.last_error_message = None

        # === ACTUALIZAR TIMESTAMPS ===
        self.updated_at = scraping.updated_at
        self.started_at = getattr(scraping, "_started_at", self.started_at)
        self.completed_at = getattr(scraping, "_completed_at", self.completed_at)

        # === ACTUALIZAR VERSIÓN ===
        self.update_version()

        if logger:
            logger.debug(
                "ScrapingModel actualizado exitosamente",
                model_id=str(self.id),
                version=self.version,
                status=self.status,
            )

    def is_active(self) -> bool:
        """Verifica si la sesión está activa."""
        return self.status in ["pending", "running"]

    def is_completed(self) -> bool:
        """Verifica si la sesión está completada."""
        return self.status in ["completed", "failed", "cancelled"]

    def calculate_progress_percentage(self) -> float:
        """Calcula el porcentaje de progreso."""
        if self.sources_count == 0:
            return 0.0

        completed = len(self.sources_completed) + len(self.sources_failed)
        return (completed / self.sources_count) * 100

    def calculate_success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        completed = len(self.sources_completed) + len(self.sources_failed)
        if completed == 0:
            return 0.0

        return (len(self.sources_completed) / completed) * 100

    def get_duration_seconds(self) -> Optional[float]:
        """Obtiene la duración de la sesión en segundos."""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    def __repr__(self) -> str:
        return f"<ScrapingModel(id={self.id}, status='{self.status}', sources={self.sources_count}, progress={self.calculate_progress_percentage():.1f}%)>"
