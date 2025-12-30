"""Domain Event: SourceScraped - Emitido cuando una source individual termina de scrapearse."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceScraped:
    """
    Evento emitido cuando una source individual termina de scrapearse.

    Este evento es escuchado por ScrapingPipeline para trackear
    el progreso del pipeline y determinar cuándo todas las sources
    han sido procesadas.

    Attributes:
        scraping_id: ID de la sesión de scraping
        source_id: ID de la source scrapeada
        success: Si el scraping fue exitoso
        articles_discovered: Artículos encontrados en el feed
        articles_created: Artículos nuevos creados
        articles_duplicated: Artículos duplicados (no creados)
        article_ids: IDs de artículos creados
        error_message: Mensaje de error si falló
        error_type: Tipo de error si falló
        duration_seconds: Duración del scraping en segundos
    """

    # Campos obligatorios
    scraping_id: str
    source_id: str
    success: bool

    # Métricas de artículos
    articles_discovered: int = 0
    articles_created: int = 0
    articles_duplicated: int = 0
    article_ids: tuple = field(default_factory=tuple)

    # Error info
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Métricas de rendimiento
    duration_seconds: float = 0.0

    # Metadatos del evento
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate para compatibilidad con IDomainEvent."""
        return self.scraping_id

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Scraping"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceScraped"

    @property
    def event_version(self) -> str:
        """Versión del evento."""
        return str(self.version)

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "scraping_id": self.scraping_id,
            "source_id": self.source_id,
            "success": self.success,
            "articles_discovered": self.articles_discovered,
            "articles_created": self.articles_created,
            "articles_duplicated": self.articles_duplicated,
            "article_ids": list(self.article_ids),
            "error_message": self.error_message,
            "error_type": self.error_type,
            "duration_seconds": self.duration_seconds,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convierte evento a diccionario."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "data": self.get_event_data(),
        }

    @classmethod
    def success_event(
        cls,
        scraping_id: str,
        source_id: str,
        articles_discovered: int,
        articles_created: int,
        article_ids: List[str],
        duration_seconds: float,
    ) -> "SourceScraped":
        """Crea evento de éxito."""
        return cls(
            scraping_id=scraping_id,
            source_id=source_id,
            success=True,
            articles_discovered=articles_discovered,
            articles_created=articles_created,
            articles_duplicated=articles_discovered - articles_created,
            article_ids=tuple(article_ids),
            duration_seconds=duration_seconds,
        )

    @classmethod
    def failure_event(
        cls,
        scraping_id: str,
        source_id: str,
        error_message: str,
        error_type: str,
        duration_seconds: float,
    ) -> "SourceScraped":
        """Crea evento de fallo."""
        return cls(
            scraping_id=scraping_id,
            source_id=source_id,
            success=False,
            error_message=error_message,
            error_type=error_type,
            duration_seconds=duration_seconds,
        )

    def __str__(self) -> str:
        if self.success:
            return (
                f"SourceScraped(source={self.source_id}, "
                f"articles={self.articles_created}/{self.articles_discovered})"
            )
        return f"SourceScraped(source={self.source_id}, failed={self.error_type})"
