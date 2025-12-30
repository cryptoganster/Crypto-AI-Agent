"""ScrapingProgress Value Object - Tracking de progreso multi-source."""

from dataclasses import dataclass, field
from typing import List, Set

from src.rss.feed.domain.value_objects import SourceId


@dataclass(frozen=True)
class ScrapingProgress:
    """
    Tracking de progreso de scraping multi-source.

    Mantiene el estado de procesamiento de múltiples sources:
    - sources_to_scrape: Lista completa de sources a procesar
    - sources_in_progress: Sources actualmente en proceso
    - sources_completed: Sources completados exitosamente
    - sources_failed: Sources que fallaron

    Este VO es inmutable. Cada cambio retorna una nueva instancia.
    """

    sources_to_scrape: List[SourceId]
    sources_in_progress: Set[SourceId] = field(default_factory=set)
    sources_completed: Set[SourceId] = field(default_factory=set)
    sources_failed: Set[SourceId] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Valida el progreso."""
        if not self.sources_to_scrape:
            raise ValueError("sources_to_scrape no puede estar vacío")

        # Validar que no haya overlaps
        all_tracked = (
            self.sources_in_progress | self.sources_completed | self.sources_failed
        )

        if len(all_tracked) > len(self.sources_to_scrape):
            raise ValueError("Hay sources tracked que no están en sources_to_scrape")

    @classmethod
    def create_new(cls, sources: List[SourceId]) -> "ScrapingProgress":
        """
        Crea progreso para una nueva sesión.

        Args:
            sources: Lista de sources a procesar

        Returns:
            ScrapingProgress con todos los sources pendientes
        """
        if not sources:
            raise ValueError("Lista de sources no puede estar vacía")

        return cls(
            sources_to_scrape=sources,
            sources_in_progress=set(),
            sources_completed=set(),
            sources_failed=set(),
        )

    def start_source(self, source_id: SourceId) -> "ScrapingProgress":
        """
        Marca un source como en progreso.

        Args:
            source_id: ID del source a iniciar

        Returns:
            Nueva ScrapingProgress con source en progreso

        Raises:
            ValueError: Si el source no está en la lista o ya está procesado
        """
        if source_id not in self.sources_to_scrape:
            raise ValueError(
                f"Source {source_id} no está en la lista de sources a procesar"
            )

        if source_id in self.sources_in_progress:
            raise ValueError(f"Source {source_id} ya está en progreso")

        if source_id in self.sources_completed:
            raise ValueError(f"Source {source_id} ya fue completado")

        if source_id in self.sources_failed:
            raise ValueError(f"Source {source_id} ya falló")

        new_in_progress = self.sources_in_progress | {source_id}

        return ScrapingProgress(
            sources_to_scrape=self.sources_to_scrape,
            sources_in_progress=new_in_progress,
            sources_completed=self.sources_completed,
            sources_failed=self.sources_failed,
        )

    def complete_source(self, source_id: SourceId) -> "ScrapingProgress":
        """
        Marca un source como completado exitosamente.

        Args:
            source_id: ID del source completado

        Returns:
            Nueva ScrapingProgress con source completado

        Raises:
            ValueError: Si el source no está en progreso
        """
        if source_id not in self.sources_in_progress:
            raise ValueError(f"Source {source_id} no está en progreso")

        new_in_progress = self.sources_in_progress - {source_id}
        new_completed = self.sources_completed | {source_id}

        return ScrapingProgress(
            sources_to_scrape=self.sources_to_scrape,
            sources_in_progress=new_in_progress,
            sources_completed=new_completed,
            sources_failed=self.sources_failed,
        )

    def fail_source(self, source_id: SourceId) -> "ScrapingProgress":
        """
        Marca un source como fallido.

        Args:
            source_id: ID del source que falló

        Returns:
            Nueva ScrapingProgress con source fallido

        Raises:
            ValueError: Si el source no está en progreso
        """
        if source_id not in self.sources_in_progress:
            raise ValueError(f"Source {source_id} no está en progreso")

        new_in_progress = self.sources_in_progress - {source_id}
        new_failed = self.sources_failed | {source_id}

        return ScrapingProgress(
            sources_to_scrape=self.sources_to_scrape,
            sources_in_progress=new_in_progress,
            sources_completed=self.sources_completed,
            sources_failed=new_failed,
        )

    def calculate_progress_percentage(self) -> float:
        """
        Calcula el porcentaje de progreso.

        Returns:
            Porcentaje de progreso (0.0 - 100.0)
        """
        total = len(self.sources_to_scrape)
        if total == 0:
            return 100.0

        processed = len(self.sources_completed) + len(self.sources_failed)
        return (processed / total) * 100.0

    def is_complete(self) -> bool:
        """
        Verifica si todos los sources fueron procesados.

        Returns:
            True si todos los sources están completados o fallidos
        """
        processed = len(self.sources_completed) + len(self.sources_failed)
        return processed == len(self.sources_to_scrape)

    def get_pending_sources(self) -> List[SourceId]:
        """
        Obtiene lista de sources pendientes (no iniciados).

        Returns:
            Lista de SourceIds pendientes
        """
        processed = (
            self.sources_in_progress | self.sources_completed | self.sources_failed
        )
        return [s for s in self.sources_to_scrape if s not in processed]

    def get_success_rate(self) -> float:
        """
        Calcula la tasa de éxito de sources procesados.

        Returns:
            Tasa de éxito (0.0 - 1.0), 0.0 si no hay procesados
        """
        processed = len(self.sources_completed) + len(self.sources_failed)
        if processed == 0:
            return 0.0

        return len(self.sources_completed) / processed

    def __str__(self) -> str:
        """Representación string."""
        progress = self.calculate_progress_percentage()
        return (
            f"ScrapingProgress("
            f"{len(self.sources_completed)}/{len(self.sources_to_scrape)} completed, "
            f"{progress:.1f}%)"
        )
