"""Source SQLAlchemy Model para Source aggregate.

Este modelo pertenece al bounded context Source y mapea el Source aggregate
a la tabla 'sources' en el schema 'crypto_news_scraper'.

Convenciones de ID:
- id: Primary Key del aggregate (UUID)
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urlparse

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.shared.infra.persistence import BaseModel
from src.shared.kernel.logger import ILogger

if TYPE_CHECKING:
    from src.rss.feed.domain.aggregates import Source
    from src.rss.feed.domain.interfaces.factories import ISourceFactory


class RssFeedModel(BaseModel):
    """
    SQLAlchemy Model para Source aggregate.

    Mapea el Source aggregate a tabla de base de datos,
    optimizado para operaciones y queries del dominio Source.

    Convenciones de ID:
    - id: Primary Key (UUID) - identificador único del Source
    """

    __tablename__ = "rss_feeds"

    # === PRIMARY KEY ===
    # Convención: 'id' como PK del aggregate
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment="Source aggregate root ID (PK)",
    )

    # === SOURCE CORE DATA ===
    name = Column(String(255), nullable=False, comment="Nombre de la fuente")
    url = Column(Text, nullable=False, comment="URL del feed")
    domain = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Dominio extraído de URL",
    )
    description = Column(Text, nullable=True, comment="Descripción de la fuente")

    # === SOURCE STATUS ===
    status = Column(
        String(20),
        default="inactive",
        nullable=False,
        index=True,
        comment="Estado: active, inactive, suspended, error",
    )

    # === SOURCE CONFIGURATION ===
    fetch_interval_minutes = Column(
        Integer,
        default=360,
        nullable=False,
        comment="Intervalo de fetch en minutos",
    )
    timeout_seconds = Column(
        Integer,
        default=30,
        nullable=False,
        comment="Timeout de conexión",
    )
    max_retries = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Intentos máximos de reintento",
    )
    user_agent = Column(
        String(255),
        nullable=True,
        comment="User agent personalizado",
    )
    follow_redirects = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Seguir redirecciones",
    )
    verify_ssl = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Verificar certificados SSL",
    )
    custom_headers = Column(
        JSONB,
        default=dict,
        comment="Headers HTTP personalizados",
    )
    configuration = Column(
        JSONB,
        nullable=True,
        comment="Configuración completa serializada (opcional)",
    )
    scraping_config = Column(
        JSONB,
        nullable=True,
        comment="Configuración especializada de scraping (ScrapingConfiguration)",
    )

    # === SOURCE METRICS ===
    total_fetch_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total de intentos de fetch",
    )
    successful_fetches = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Fetches exitosos",
    )
    failed_fetches = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Fetches fallidos",
    )
    last_fetch_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Último fetch",
    )
    last_successful_fetch_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Último fetch exitoso",
    )
    average_response_time_ms = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Tiempo de respuesta promedio",
    )

    # === ERROR HANDLING ===
    consecutive_failures = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Fallos consecutivos",
    )
    last_error_message = Column(
        Text,
        nullable=True,
        comment="Último mensaje de error",
    )
    last_error_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fecha del último error",
    )

    # === DISCOVERY METRICS ===
    total_articles_discovered = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total de artículos descubiertos",
    )
    last_articles_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Artículos en último fetch",
    )

    # === PERFORMANCE INDEXES ===
    __table_args__ = (
        # Deduplicación por URL única
        Index("idx_sources_url_unique", "url", unique=True),
        # Performance queries: Fuentes activas
        Index("idx_sources_status", "status"),
        # Analytics queries: Agrupación por dominio
        Index("idx_sources_domain_status", "domain", "status"),
        # Scheduling queries: Sources listas para fetch
        Index(
            "idx_sources_fetch_due",
            "last_fetch_at",
            "status",
            "fetch_interval_minutes",
        ),
        # Error analysis: Sources con errores
        Index(
            "idx_sources_errors",
            "consecutive_failures",
            "last_error_at",
        ),
        # Health monitoring: Success rate analysis
        Index(
            "idx_sources_health",
            "successful_fetches",
            "failed_fetches",
            "status",
        ),
        # Time-based indexes
        Index("idx_sources_created_at", "created_at"),
        Index("idx_sources_updated_at", "updated_at"),
        # Schema configuration
        {"schema": "crypto_news_scraper"},
    )

    def __init__(self, **kwargs):
        """Constructor con logging inyectado."""
        super().__init__(**kwargs)
        self._logger: ILogger = kwargs.get("logger")

    def record_successful_fetch(
        self, articles_discovered: int, response_time_ms: float
    ) -> None:
        """Registra un fetch exitoso con métricas."""
        now = datetime.now(timezone.utc)

        self.successful_fetches += 1
        self.total_fetch_attempts += 1
        self.last_fetch_at = now
        self.last_successful_fetch_at = now
        self.last_articles_count = articles_discovered
        self.total_articles_discovered += articles_discovered
        self.consecutive_failures = 0

        # Actualizar tiempo promedio (media móvil simple)
        if self.average_response_time_ms == 0:
            self.average_response_time_ms = response_time_ms
        else:
            self.average_response_time_ms = (
                self.average_response_time_ms + response_time_ms
            ) / 2

        # Limpiar error anterior
        self.last_error_message = None
        self.last_error_at = None

        self.updated_at = now
        self.update_version()

    def record_failed_fetch(self, error_message: str) -> None:
        """Registra un fetch fallido con tracking de errores."""
        now = datetime.now(timezone.utc)

        self.failed_fetches += 1
        self.total_fetch_attempts += 1
        self.last_fetch_at = now
        self.consecutive_failures += 1

        self.last_error_message = (
            error_message[:1000] if error_message else "Unknown error"
        )
        self.last_error_at = now

        self.updated_at = now
        self.update_version()

    def calculate_success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_fetch_attempts == 0:
            return 1.0
        return self.successful_fetches / self.total_fetch_attempts

    def is_healthy(self) -> bool:
        """Determina si la source está saludable."""
        success_rate = self.calculate_success_rate()

        recent_error = (
            self.last_error_at
            and (datetime.now(timezone.utc) - self.last_error_at).total_seconds()
            < 86400
        )

        return (
            success_rate >= 0.8
            and self.consecutive_failures < 5
            and (not recent_error or success_rate >= 0.9)
        )

    def is_due_for_fetch(self) -> bool:
        """Determina si la source está lista para fetch."""
        if self.status != "active":
            return False

        if self.last_fetch_at is None:
            return True

        next_fetch = self.last_fetch_at + timedelta(minutes=self.fetch_interval_minutes)

        if self.consecutive_failures > 3:
            backoff_multiplier = min(2 ** (self.consecutive_failures - 3), 8)
            next_fetch += timedelta(
                minutes=self.fetch_interval_minutes * backoff_multiplier
            )

        return datetime.now(timezone.utc) >= next_fetch

    @property
    def is_active(self) -> bool:
        """Verifica si la source está activa."""
        return self.status == "active"

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extrae el dominio de una URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if domain.startswith("www."):
                domain = domain[4:]

            return domain[:100]

        except Exception:
            return "unknown"

    def get_health_status(self) -> str:
        """Obtiene el status de salud como string."""
        if not self.is_active:
            return "INACTIVE"
        elif self.is_healthy():
            return "HEALTHY"
        elif self.calculate_success_rate() >= 0.5:
            return "DEGRADED"
        else:
            return "UNHEALTHY"

    def to_source_domain(
        self, source_factory: "ISourceFactory" = None, logger: Optional[ILogger] = None
    ) -> "Source":
        """
        Reconstruye el Source aggregate desde el modelo.

        DELEGADO A SourceMapper.to_domain() para asegurar deserialización completa.

        Args:
            source_factory: (Deprecado) Factory para reconstruir agregados
            logger: Logger para observabilidad

        Returns:
            Source: Aggregate reconstruido
        """
        if logger:
            logger.debug(
                "Reconstruyendo Source aggregate delegando a SourceMapper",
                model_id=str(self.id),
                domain=self.domain,
                status=self.status,
            )

        from src.rss.feed.infra.persistence.mappers import SourceMapper

        source = SourceMapper.to_domain(self)

        if logger:
            logger.debug(
                "Source aggregate reconstruido exitosamente",
                source_id=str(source.id),
                name=source.name,
                status=source.status,
                has_scraping_config=source.scraping_config is not None,
            )

        return source

    def __repr__(self) -> str:
        return f"<SourceModel(id={self.id}, domain='{self.domain}', active={self.is_active}, health='{self.get_health_status()}')>"
