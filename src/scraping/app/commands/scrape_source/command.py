"""Comando ScrapeSource - Scrapea una única source RSS."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class ScrapeSourceCommand:
    """
    Comando para scrapear una única source RSS.

    Este es un comando simple que sigue CQRS estricto:
    - Un agregado (Source)
    - Una operación (scrape)
    - Emite evento al completar (SourceScraped)

    El ScrapingPipeline emite este comando para cada source
    que necesita ser scrapeada, pasando las opciones de scraping
    que recibió del evento ScrapingStarted.

    Attributes:
        source_id: ID de la source a scrapear
        pipeline_id: ID del pipeline que solicitó el scraping
        timeout_seconds: Timeout para la operación
        quality_threshold: Umbral mínimo de calidad (None = sin filtro)
        enable_deduplication: Activar detección de duplicados
        force_refresh: Forzar re-scraping ignorando caché
        max_items: Límite de artículos a obtener
        priority_mode: Modo de prioridad (normal, high, low)
        correlation_id: ID de correlación para tracking

    Example:
        >>> command = ScrapeSourceCommand(
        ...     source_id="src-123",
        ...     pipeline_id="pipeline-456",
        ...     quality_threshold=0.7,
        ... )
    """

    # Identificadores
    source_id: str
    pipeline_id: Optional[str] = None

    # Opciones de scraping (heredadas del pipeline)
    timeout_seconds: int = 30
    quality_threshold: Optional[float] = None
    enable_deduplication: bool = True
    force_refresh: bool = False
    max_items: Optional[int] = None

    # Control de ejecución
    priority_mode: str = "normal"
    correlation_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        """Valida el comando."""
        if not self.source_id:
            raise ValueError("source_id es requerido")

        if self.priority_mode not in ("normal", "high", "low"):
            raise ValueError(
                f"priority_mode debe ser 'normal', 'high' o 'low', "
                f"recibido: {self.priority_mode}"
            )

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser mayor a 0")

        if self.quality_threshold is not None:
            if not (0.0 <= self.quality_threshold <= 1.0):
                raise ValueError("quality_threshold debe estar entre 0.0 y 1.0")
