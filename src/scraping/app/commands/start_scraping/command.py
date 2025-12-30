"""Comando para iniciar scraping de sources RSS."""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class StartScrapingCommand:
    """
    Comando para iniciar scraping de sources RSS.

    Este comando inicia el pipeline de scraping. El handler:
    1. Valida el comando
    2. Resuelve sources (por IDs, URLs, o todas activas)
    3. Crea sesión de scraping
    4. Emite evento ScrapingStarted (con opciones)

    El ScrapingPipeline escucha el evento y coordina el resto.

    Attributes:
        source_ids: IDs de sources a scrapear (None = todas activas)
        source_urls: URLs de sources a scrapear (alternativa a source_ids)
        max_concurrent: Máximo de scraping concurrentes
        timeout_seconds: Timeout por source
        quality_threshold: Umbral mínimo de calidad (None = sin filtro)
        enable_quality_filter: Activar filtro de calidad
        enable_deduplication: Activar detección de duplicados
        force_refresh: Forzar re-scraping ignorando caché
        max_items_per_source: Límite de artículos por source
        correlation_id: ID para tracking
        triggered_by: Origen del trigger
        session_name: Nombre descriptivo de la sesión

    Example:
        >>> # Scrapear sources específicas por ID
        >>> command = StartScrapingCommand(source_ids=["src-1", "src-2"])
        >>>
        >>> # Scrapear sources por URL
        >>> command = StartScrapingCommand(source_urls=["https://example.com/feed"])
        >>>
        >>> # Scrapear todas las activas con filtro de calidad
        >>> command = StartScrapingCommand(quality_threshold=0.7)
    """

    # Identificadores de sources
    source_ids: Optional[List[str]] = None
    source_urls: Optional[List[str]] = None

    # Configuración de concurrencia
    max_concurrent: int = 5
    timeout_seconds: int = 30

    # Opciones de scraping
    quality_threshold: Optional[float] = None
    enable_quality_filter: bool = True
    enable_deduplication: bool = True
    force_refresh: bool = False
    max_items_per_source: Optional[int] = None

    # Metadatos
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    triggered_by: str = "manual"  # manual, scheduler, api, health_recovery
    session_name: Optional[str] = None

    def __post_init__(self):
        """Valida el comando."""
        if self.max_concurrent <= 0:
            raise ValueError("max_concurrent debe ser mayor a 0")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser mayor a 0")

        if self.quality_threshold is not None:
            if not (0.0 <= self.quality_threshold <= 1.0):
                raise ValueError("quality_threshold debe estar entre 0.0 y 1.0")

        valid_triggers = {"manual", "scheduler", "api", "health_recovery"}
        if self.triggered_by not in valid_triggers:
            raise ValueError(f"triggered_by debe ser uno de: {valid_triggers}")

        # Normalizar listas vacías a None
        if self.source_ids is not None:
            filtered = [sid for sid in self.source_ids if sid]
            object.__setattr__(self, "source_ids", filtered if filtered else None)

        if self.source_urls is not None:
            filtered = [url for url in self.source_urls if url]
            object.__setattr__(self, "source_urls", filtered if filtered else None)

    @property
    def is_all_sources(self) -> bool:
        """Indica si es scraping de todas las sources activas."""
        return not self.source_ids and not self.source_urls

    @property
    def is_single_source(self) -> bool:
        """Indica si es scraping de una sola source."""
        if self.source_ids:
            return len(self.source_ids) == 1
        if self.source_urls:
            return len(self.source_urls) == 1
        return False
