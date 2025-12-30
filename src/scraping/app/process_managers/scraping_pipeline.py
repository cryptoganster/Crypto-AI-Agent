"""ScrapingPipeline - Orquestador event-driven para scraping de sources.

Este Process Manager coordina el flujo de scraping:
1. Escucha: ScrapingStarted (con opciones de scraping)
2. Emite: ScrapeSourceCommand (por cada source, con opciones)
3. Escucha: SourceScraped (por cada source)
4. Emite: ScrapingCompleted (cuando todas terminan)

Sigue CQRS estricto:
- NO hace queries directas
- NO llama handlers directamente
- SÍ escucha eventos
- SÍ emite comandos

Las opciones de scraping fluyen desde el evento ScrapingStarted
hacia cada ScrapeSourceCommand, manteniendo la arquitectura event-driven.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from src.scraping.domain.events import (
    ScrapingCompleted,
    ScrapingStarted,
    SourceScraped,
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


@dataclass
class ScrapingOptions:
    """Opciones de scraping transportadas desde el evento."""

    timeout_seconds: int = 30
    quality_threshold: Optional[float] = None
    enable_quality_filter: bool = True
    enable_deduplication: bool = True
    force_refresh: bool = False
    max_items_per_source: Optional[int] = None


@dataclass
class PipelineState:
    """Estado interno del pipeline de scraping."""

    scraping_id: str
    source_ids: List[str]
    max_concurrent: int
    options: ScrapingOptions
    completed_sources: Set[str] = field(default_factory=set)
    failed_sources: Set[str] = field(default_factory=set)
    articles_by_source: Dict[str, int] = field(default_factory=dict)
    article_ids: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_complete(self) -> bool:
        """Indica si todas las sources han sido procesadas."""
        processed = self.completed_sources | self.failed_sources
        return len(processed) >= len(self.source_ids)

    @property
    def total_articles(self) -> int:
        """Total de artículos creados."""
        return sum(self.articles_by_source.values())

    @property
    def success_count(self) -> int:
        """Número de sources exitosas."""
        return len(self.completed_sources)

    @property
    def failed_count(self) -> int:
        """Número de sources fallidas."""
        return len(self.failed_sources)


class ScrapingPipeline:
    """
    Process Manager para el pipeline de scraping de sources.

    Orquesta el flujo de scraping de forma event-driven:

    1. on_scraping_started() - Recibe evento con opciones, emite ScrapeSourceCommand
    2. on_source_scraped() - Recibe evento, trackea progreso
    3. Cuando todas completan → emite ScrapingCompleted

    Responsabilidades:
    - Escuchar eventos de dominio
    - Emitir comandos al bus (con opciones de scraping)
    - Trackear estado del pipeline
    - Emitir evento de completado

    NO hace:
    - Queries directas a repositorios
    - Llamadas directas a handlers
    - Lógica de negocio

    Las opciones de scraping (quality_threshold, enable_deduplication, etc.)
    se leen del evento ScrapingStarted y se pasan a cada ScrapeSourceCommand.
    """

    def __init__(
        self,
        command_bus: IMediator,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        self._command_bus = command_bus
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application",
            component="ScrapingPipeline",
        )

        # Estado de pipelines activos (en memoria)
        self._active_pipelines: Dict[str, PipelineState] = {}

    async def on_scraping_started(self, event: ScrapingStarted) -> None:
        """
        Maneja el evento ScrapingStarted.

        Lee las opciones de scraping del evento, crea estado del pipeline,
        y emite ScrapeSourceCommand para cada source con las opciones.

        Args:
            event: Evento de scraping iniciado (con opciones)
        """
        self._logger.info(
            "ScrapingPipeline: ScrapingStarted recibido",
            scraping_id=event.scraping_id,
            sources_count=event.sources_count,
            max_concurrent=event.max_concurrent,
            quality_threshold=event.quality_threshold,
            enable_deduplication=event.enable_deduplication,
        )

        # Obtener source_ids del evento (ahora vienen incluidos)
        source_ids = list(event.source_ids) if event.source_ids else []

        if not source_ids:
            self._logger.warning(
                "No hay sources en el evento ScrapingStarted",
                scraping_id=event.scraping_id,
            )
            return

        # Extraer opciones de scraping del evento
        options = ScrapingOptions(
            timeout_seconds=event.timeout_seconds,
            quality_threshold=event.quality_threshold,
            enable_quality_filter=event.enable_quality_filter,
            enable_deduplication=event.enable_deduplication,
            force_refresh=event.force_refresh,
            max_items_per_source=event.max_items_per_source,
        )

        # Crear estado del pipeline con opciones
        state = PipelineState(
            scraping_id=event.scraping_id,
            source_ids=source_ids,
            max_concurrent=event.max_concurrent,
            options=options,
        )
        self._active_pipelines[event.scraping_id] = state

        self._logger.info(
            "Pipeline state creado",
            scraping_id=event.scraping_id,
            sources_count=len(source_ids),
            options=vars(options),
        )

        # Emitir ScrapeSourceCommand para cada source (con opciones)
        from src.scraping.app.commands.scrape_source.command import ScrapeSourceCommand

        for source_id in source_ids:
            try:
                # Pasar opciones de scraping al comando
                command = ScrapeSourceCommand(
                    source_id=source_id,
                    pipeline_id=event.scraping_id,
                    timeout_seconds=options.timeout_seconds,
                    quality_threshold=options.quality_threshold,
                    enable_deduplication=options.enable_deduplication,
                    force_refresh=options.force_refresh,
                    max_items=options.max_items_per_source,
                )

                await self._command_bus.send(command)

                self._logger.debug(
                    "ScrapeSourceCommand emitido",
                    scraping_id=event.scraping_id,
                    source_id=source_id,
                    quality_threshold=options.quality_threshold,
                )

            except Exception as e:
                self._logger.error(
                    "Error emitiendo ScrapeSourceCommand",
                    scraping_id=event.scraping_id,
                    source_id=source_id,
                    error=str(e),
                )
                state.failed_sources.add(source_id)

        # Verificar si ya completó (todas fallaron al emitir)
        if state.is_complete:
            await self._handle_pipeline_completed(event.scraping_id)

    async def on_source_scraped(self, event: SourceScraped) -> None:
        """
        Maneja el evento SourceScraped.

        Actualiza estado del pipeline y verifica si está completo.

        Args:
            event: Evento de source scrapeada
        """
        state = self._active_pipelines.get(event.scraping_id)

        if not state:
            self._logger.warning(
                "Pipeline no encontrado para SourceScraped",
                scraping_id=event.scraping_id,
                source_id=event.source_id,
            )
            return

        # Actualizar estado
        if event.success:
            state.completed_sources.add(event.source_id)
            state.articles_by_source[event.source_id] = event.articles_created
            state.article_ids.extend(event.article_ids)

            self._logger.info(
                f"🔍 DEBUG: Source scrapeada - Estado actualizado | "
                f"source={event.source_id} | "
                f"articles_created={event.articles_created} | "
                f"articles_discovered={event.articles_discovered} | "
                f"total_articles_in_state={state.total_articles}"
            )
        else:
            state.failed_sources.add(event.source_id)

            self._logger.error(
                "❌ Source falló al scrapear - Pipeline",
                scraping_id=event.scraping_id,
                source_id=event.source_id,
                error_message=event.error_message,
                error_type=getattr(event, "error_type", None),
                articles_discovered=event.articles_discovered,
                articles_created=event.articles_created,
                duration_seconds=getattr(event, "duration_seconds", 0.0),
            )

        # Verificar si el pipeline está completo
        if state.is_complete:
            await self._handle_pipeline_completed(event.scraping_id)

    async def _handle_pipeline_completed(self, scraping_id: str) -> None:
        """
        Maneja la completación del pipeline.

        Emite evento ScrapingCompleted y limpia estado.

        Args:
            scraping_id: ID del scraping completado
        """
        state = self._active_pipelines.get(scraping_id)

        if not state:
            return

        duration = (datetime.now(timezone.utc) - state.started_at).total_seconds()

        self._logger.info(
            "Pipeline de scraping completado",
            scraping_id=scraping_id,
            duration_seconds=duration,
            sources_total=len(state.source_ids),
            sources_success=state.success_count,
            sources_failed=state.failed_count,
            total_articles=state.total_articles,
        )

        # Emitir evento ScrapingCompleted
        event = ScrapingCompleted(
            aggregate_id=scraping_id,
            source_id=state.source_ids[0] if state.source_ids else "none",
            scraping_id=scraping_id,
            final_status="completed" if state.failed_count == 0 else "partial",
            sources_processed=len(state.source_ids),
            sources_successful=state.success_count,
            sources_failed=state.failed_count,
            articles_discovered=state.total_articles,
            articles_new=state.total_articles,
            duration_seconds=duration,
        )

        self._logger.info(
            f"🔍 DEBUG: Emitiendo ScrapingCompleted | "
            f"scraping_id={scraping_id} | "
            f"articles_new={state.total_articles} | "
            f"articles_by_source={state.articles_by_source} | "
            f"article_ids_count={len(state.article_ids)}"
        )

        await self._event_bus.publish(event)

        self._logger.info(
            "Evento ScrapingCompleted emitido",
            scraping_id=scraping_id,
            articles_total=state.total_articles,
        )

        # Limpiar estado
        del self._active_pipelines[scraping_id]

    def get_pipeline_status(self, scraping_id: str) -> Optional[Dict]:
        """
        Obtiene el estado actual de un pipeline.

        Args:
            scraping_id: ID del scraping

        Returns:
            Dict con estado o None si no existe
        """
        state = self._active_pipelines.get(scraping_id)

        if not state:
            return None

        return {
            "scraping_id": state.scraping_id,
            "sources_total": len(state.source_ids),
            "sources_completed": state.success_count,
            "sources_failed": state.failed_count,
            "sources_pending": (
                len(state.source_ids)
                - len(state.completed_sources)
                - len(state.failed_sources)
            ),
            "total_articles": state.total_articles,
            "is_complete": state.is_complete,
            "started_at": state.started_at.isoformat(),
        }
