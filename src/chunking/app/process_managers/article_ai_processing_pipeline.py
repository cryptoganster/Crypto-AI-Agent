"""Process Manager para el pipeline de procesamiento AI de artículos."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional

from src.chunking.app.commands.chunk_article.command import ChunkArticleCommand
from src.chunking.app.commands.generate_chunk_embeddings.command import (
    GenerateChunkEmbeddingsCommand,
)
from src.chunking.app.commands.generate_chunk_summaries.command import (
    GenerateChunkSummariesCommand,
)
from src.chunking.app.commands.generate_global_summary.command import (
    GenerateGlobalSummaryCommand,
)
from src.chunking.app.commands.generate_tldr.command import GenerateTLDRCommand
from src.chunking.app.commands.persist_chunks.command import PersistChunksCommand
from src.chunking.domain.events import (
    ArticleAIProcessedEvent,
    ChunkCompletedEvent,
    ChunkCreatedEvent,
    ChunkEmbeddedEvent,
    ChunkFailedEvent,
    ChunkSummarizedEvent,
)
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


class PipelineState(str, Enum):
    """Estados del pipeline de procesamiento."""

    PENDING = "pending"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    SUMMARIZING = "summarizing"
    PERSISTING = "persisting"
    GLOBAL_SUMMARY = "global_summary"
    TLDR = "tldr"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineMetrics:
    """Métricas del procesamiento del pipeline."""

    total_chunks: int = 0
    chunks_created: int = 0
    chunks_embedded: int = 0
    chunks_summarized: int = 0
    chunks_completed: int = 0
    chunks_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_chunking_complete(self) -> bool:
        """Indica si el chunking está completo."""
        return self.chunks_created == self.total_chunks and self.total_chunks > 0

    @property
    def is_embedding_complete(self) -> bool:
        """Indica si el embedding está completo."""
        return self.chunks_embedded == self.total_chunks and self.total_chunks > 0

    @property
    def is_summarizing_complete(self) -> bool:
        """Indica si la summarización está completa."""
        return self.chunks_summarized == self.total_chunks and self.total_chunks > 0

    @property
    def is_persistence_complete(self) -> bool:
        """Indica si la persistencia está completa."""
        return self.chunks_completed == self.total_chunks and self.total_chunks > 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duración del procesamiento en segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class ArticlePipelineState:
    """Estado del pipeline para un artículo específico."""

    article_id: str
    state: PipelineState = PipelineState.PENDING
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)
    error_message: Optional[str] = None
    enable_global_summary: bool = True
    enable_tldr: bool = True

    # Datos necesarios para pasos posteriores
    article_text: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "rss_article"  # Default to rss_article
    published_at: Optional[str] = None

    def mark_failed(self, error: str) -> None:
        """Marca el pipeline como fallido."""
        self.state = PipelineState.FAILED
        self.error_message = error
        self.metrics.completed_at = datetime.now(timezone.utc)


class ArticleAIProcessingPipeline:
    """
    Process Manager para el pipeline de procesamiento AI.

    Coordina el flujo event-driven de procesamiento de artículos:
    1. Chunking
    2. Embeddings
    3. Summaries
    4. Persistence
    5. Global Summary (opcional)
    6. TLDR (opcional)

    Responsabilidades:
    - Escuchar eventos de dominio
    - Emitir comandos al bus
    - Mantener estado del proceso por artículo
    - Trackear métricas de procesamiento
    """

    def __init__(
        self,
        command_bus: IMediator,
        event_bus: IMediator,
        logger: ILogger,
        enable_global_summary: bool = True,
        enable_tldr: bool = True,
        max_chunk_failures: int = 3,
        abort_on_failure: bool = False,
    ):
        """
        Inicializa el Process Manager.

        Args:
            command_bus: Mediator para enviar comandos
            event_bus: Mediator para publicar eventos
            logger: Logger para registrar eventos
            enable_global_summary: Si generar summary global
            enable_tldr: Si generar TLDR
            max_chunk_failures: Máximo de fallos de chunks antes de abortar
            abort_on_failure: Si abortar pipeline al primer fallo
        """
        self._command_bus = command_bus
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application",
            component="ArticleAIProcessingPipeline",
        )
        self._enable_global_summary = enable_global_summary
        self._enable_tldr = enable_tldr
        self._max_chunk_failures = max_chunk_failures
        self._abort_on_failure = abort_on_failure

        # Estado del pipeline por artículo
        self._pipelines: Dict[str, ArticlePipelineState] = {}

    async def start_pipeline(
        self,
        article_id: str,
        article_text: str,
        source_url: str,
        source_type: str = "rss_article",
        published_at: Optional[str] = None,
        enable_global_summary: Optional[bool] = None,
        enable_tldr: Optional[bool] = None,
    ) -> None:
        """
        Inicia el pipeline de procesamiento para un artículo.

        Args:
            article_id: ID del artículo
            article_text: Texto completo del artículo
            source_url: URL de la fuente
            source_type: Tipo de fuente (rss_article, web_scrape, etc.)
            published_at: Fecha de publicación (ISO format)
            enable_global_summary: Override para global summary
            enable_tldr: Override para TLDR
        """
        self._logger.info(
            "Iniciando pipeline de procesamiento AI",
            article_id=article_id,
            text_length=len(article_text),
        )

        # Crear estado del pipeline
        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.CHUNKING,
            article_text=article_text,
            source_url=source_url,
            source_type=source_type,
            published_at=published_at,
            enable_global_summary=(
                enable_global_summary
                if enable_global_summary is not None
                else self._enable_global_summary
            ),
            enable_tldr=(enable_tldr if enable_tldr is not None else self._enable_tldr),
        )
        pipeline_state.metrics.started_at = datetime.now(timezone.utc)

        self._pipelines[article_id] = pipeline_state

        # Emitir comando de chunking
        await self._emit_chunk_article_command(article_id)

    def set_total_chunks(self, article_id: str, total_chunks: int) -> None:
        """
        Establece el número total de chunks para un artículo.

        Este método debe ser llamado después de que ChunkArticleCommand se complete.

        Args:
            article_id: ID del artículo
            total_chunks: Número total de chunks creados
        """
        pipeline = self._pipelines.get(article_id)
        if pipeline:
            pipeline.metrics.total_chunks = total_chunks
            self._logger.debug(
                "Total de chunks establecido",
                article_id=article_id,
                total_chunks=total_chunks,
            )

    async def on_chunk_created(self, event: ChunkCreatedEvent) -> None:
        """
        Maneja evento ChunkCreated.

        Incrementa contador de chunks creados.
        Cuando todos los chunks están creados → Emite GenerateChunkEmbeddingsCommand.

        Args:
            event: Evento ChunkCreated
        """
        article_id = event.article_id
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para ChunkCreated",
                article_id=article_id,
                chunk_id=event.chunk_id,
            )
            return

        # Incrementar contador
        pipeline.metrics.chunks_created += 1

        self._logger.debug(
            "Chunk creado",
            article_id=article_id,
            chunk_id=event.chunk_id,
            position=event.position,
            chunks_created=pipeline.metrics.chunks_created,
            total_chunks=pipeline.metrics.total_chunks,
        )

        # Si todos los chunks están creados, pasar a embeddings
        if pipeline.metrics.is_chunking_complete:
            await self._emit_generate_embeddings_command(article_id)

    async def on_chunk_embedded(self, event: ChunkEmbeddedEvent) -> None:
        """
        Maneja evento ChunkEmbedded.

        Incrementa contador de chunks embedded.
        Cuando todos los chunks están embedded → Emite GenerateChunkSummariesCommand.

        Args:
            event: Evento ChunkEmbedded
        """
        article_id = event.article_id
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para ChunkEmbedded",
                article_id=article_id,
                chunk_id=event.chunk_id,
            )
            return

        # Incrementar contador
        pipeline.metrics.chunks_embedded += 1

        self._logger.debug(
            "Chunk embedded",
            article_id=article_id,
            chunk_id=event.chunk_id,
            chunks_embedded=pipeline.metrics.chunks_embedded,
            total_chunks=pipeline.metrics.total_chunks,
        )

        # Si todos los chunks están embedded, pasar a summaries
        if pipeline.metrics.is_embedding_complete:
            await self._emit_generate_summaries_command(article_id)

    async def on_chunk_summarized(self, event: ChunkSummarizedEvent) -> None:
        """
        Maneja evento ChunkSummarized.

        Incrementa contador de chunks summarized.
        Cuando todos los chunks están summarized → Emite PersistChunksCommand.

        Args:
            event: Evento ChunkSummarized
        """
        article_id = event.article_id
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para ChunkSummarized",
                article_id=article_id,
                chunk_id=event.chunk_id,
            )
            return

        # Incrementar contador
        pipeline.metrics.chunks_summarized += 1

        self._logger.debug(
            "Chunk summarized",
            article_id=article_id,
            chunk_id=event.chunk_id,
            chunks_summarized=pipeline.metrics.chunks_summarized,
            total_chunks=pipeline.metrics.total_chunks,
        )

        # Si todos los chunks están summarized, pasar a persistencia
        if pipeline.metrics.is_summarizing_complete:
            await self._emit_persist_chunks_command(article_id)

    async def on_chunk_completed(self, event: ChunkCompletedEvent) -> None:
        """
        Maneja evento ChunkCompleted.

        Incrementa contador de chunks completed.
        Cuando todos los chunks están completed → Emite GenerateGlobalSummaryCommand (si habilitado).

        Args:
            event: Evento ChunkCompleted
        """
        article_id = event.article_id
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para ChunkCompleted",
                article_id=article_id,
                chunk_id=event.chunk_id,
            )
            return

        # Incrementar contador
        pipeline.metrics.chunks_completed += 1

        self._logger.debug(
            "Chunk completed",
            article_id=article_id,
            chunk_id=event.chunk_id,
            chunks_completed=pipeline.metrics.chunks_completed,
            total_chunks=pipeline.metrics.total_chunks,
        )

        # Si todos los chunks están completed, pasar a global summary o completar
        if pipeline.metrics.is_persistence_complete:
            if pipeline.enable_global_summary:
                await self._emit_generate_global_summary_command(article_id)
            elif pipeline.enable_tldr:
                await self._emit_generate_tldr_command(article_id)
            else:
                await self._complete_pipeline(article_id)

    async def on_chunk_failed(self, event: ChunkFailedEvent) -> None:
        """
        Maneja evento ChunkFailed.

        Incrementa contador de chunks fallidos.
        Decide si continuar o abortar pipeline según configuración.

        Args:
            event: Evento ChunkFailed
        """
        article_id = event.article_id
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para ChunkFailed",
                article_id=article_id,
                chunk_id=event.chunk_id,
            )
            return

        # Incrementar contador de fallos
        pipeline.metrics.chunks_failed += 1

        self._logger.warning(
            "Chunk falló",
            article_id=article_id,
            chunk_id=event.chunk_id,
            error=event.error_message,
            chunks_failed=pipeline.metrics.chunks_failed,
            max_failures=self._max_chunk_failures,
        )

        # Decidir si abortar pipeline
        should_abort = (
            self._abort_on_failure
            or pipeline.metrics.chunks_failed >= self._max_chunk_failures
        )

        if should_abort:
            error_msg = (
                f"Pipeline abortado: {pipeline.metrics.chunks_failed} chunks fallidos. "
                f"Último error: {event.error_message}"
            )
            await self._fail_pipeline(article_id, error_msg)
        else:
            self._logger.info(
                "Continuando pipeline a pesar del fallo",
                article_id=article_id,
                chunks_failed=pipeline.metrics.chunks_failed,
                max_failures=self._max_chunk_failures,
            )

    async def on_global_summary_generated(self, article_id: str) -> None:
        """
        Maneja generación de global summary.

        Si TLDR está habilitado → Emite GenerateTLDRCommand.
        Si no → Completa pipeline.

        Args:
            article_id: ID del artículo
        """
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para GlobalSummaryGenerated",
                article_id=article_id,
            )
            return

        self._logger.info(
            "Global summary generado",
            article_id=article_id,
        )

        # Si TLDR está habilitado, generarlo
        if pipeline.enable_tldr:
            await self._emit_generate_tldr_command(article_id)
        else:
            await self._complete_pipeline(article_id)

    async def on_tldr_generated(self, article_id: str) -> None:
        """
        Maneja generación de TLDR.

        Completa el pipeline.

        Args:
            article_id: ID del artículo
        """
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para TLDRGenerated",
                article_id=article_id,
            )
            return

        self._logger.info(
            "TLDR generado",
            article_id=article_id,
        )

        await self._complete_pipeline(article_id)

    async def on_pipeline_failed(self, article_id: str, error: str) -> None:
        """
        Maneja fallo del pipeline (método público para handlers externos).

        Args:
            article_id: ID del artículo
            error: Mensaje de error
        """
        await self._fail_pipeline(article_id, error)

    # Métodos privados para emitir comandos

    async def _emit_chunk_article_command(self, article_id: str) -> None:
        """Emite comando ChunkArticle."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.CHUNKING

        command = ChunkArticleCommand(
            article_id=article_id,
            text=pipeline.article_text,
            source_url=pipeline.source_url,
            source_type=pipeline.source_type,
            published_at=pipeline.published_at,
        )

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "ChunkArticleCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ChunkArticleCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en chunking: {str(e)}")

    async def _emit_generate_embeddings_command(self, article_id: str) -> None:
        """Emite comando GenerateChunkEmbeddings."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.EMBEDDING

        command = GenerateChunkEmbeddingsCommand(article_id=article_id)

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "GenerateChunkEmbeddingsCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo GenerateChunkEmbeddingsCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en embeddings: {str(e)}")

    async def _emit_generate_summaries_command(self, article_id: str) -> None:
        """Emite comando GenerateChunkSummaries."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.SUMMARIZING

        command = GenerateChunkSummariesCommand(article_id=article_id)

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "GenerateChunkSummariesCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo GenerateChunkSummariesCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en summaries: {str(e)}")

    async def _emit_persist_chunks_command(self, article_id: str) -> None:
        """Emite comando PersistChunks."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.PERSISTING

        command = PersistChunksCommand(article_id=article_id)

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "PersistChunksCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo PersistChunksCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en persistencia: {str(e)}")

    async def _emit_generate_global_summary_command(self, article_id: str) -> None:
        """Emite comando GenerateGlobalSummary."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.GLOBAL_SUMMARY

        command = GenerateGlobalSummaryCommand(article_id=article_id)

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "GenerateGlobalSummaryCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo GenerateGlobalSummaryCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en global summary: {str(e)}")

    async def _emit_generate_tldr_command(self, article_id: str) -> None:
        """Emite comando GenerateTLDR."""
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.TLDR

        command = GenerateTLDRCommand(article_id=article_id)

        try:
            await self._command_bus.send(command)
            self._logger.info(
                "GenerateTLDRCommand emitido",
                article_id=article_id,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo GenerateTLDRCommand",
                article_id=article_id,
                error=str(e),
            )
            await self._fail_pipeline(article_id, f"Error en TLDR: {str(e)}")

    async def _complete_pipeline(self, article_id: str) -> None:
        """
        Completa el pipeline exitosamente.

        Emite ArticleAIProcessedEvent con success=True.
        """
        pipeline = self._pipelines[article_id]
        pipeline.state = PipelineState.COMPLETED
        pipeline.metrics.completed_at = datetime.now(timezone.utc)

        self._logger.info(
            "Pipeline completado exitosamente",
            article_id=article_id,
            duration_seconds=pipeline.metrics.duration_seconds,
            total_chunks=pipeline.metrics.total_chunks,
            chunks_failed=pipeline.metrics.chunks_failed,
        )

        # Emitir evento de completitud
        event = ArticleAIProcessedEvent(
            article_id=article_id,
            chunks_created=pipeline.metrics.total_chunks,
            total_tokens=0,  # TODO: Calcular total de tokens
            has_global_summary=pipeline.enable_global_summary,
            has_tldr=pipeline.enable_tldr,
            success=True,
        )

        try:
            await self._event_bus.publish(event)
            self._logger.info(
                "ArticleAIProcessedEvent emitido",
                article_id=article_id,
                success=True,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ArticleAIProcessedEvent",
                article_id=article_id,
                error=str(e),
            )

        # Limpiar estado del pipeline
        del self._pipelines[article_id]

    async def _fail_pipeline(self, article_id: str, error: str) -> None:
        """
        Falla el pipeline.

        Emite ArticleAIProcessedEvent con success=False.

        Args:
            article_id: ID del artículo
            error: Mensaje de error
        """
        pipeline = self._pipelines.get(article_id)

        if not pipeline:
            self._logger.warning(
                "Pipeline no encontrado para fallo",
                article_id=article_id,
            )
            return

        pipeline.mark_failed(error)

        self._logger.error(
            "Pipeline fallido",
            article_id=article_id,
            error=error,
            state=pipeline.state.value,
            chunks_created=pipeline.metrics.chunks_created,
            chunks_failed=pipeline.metrics.chunks_failed,
        )

        # Emitir evento de fallo
        event = ArticleAIProcessedEvent(
            article_id=article_id,
            chunks_created=pipeline.metrics.chunks_created,
            total_tokens=0,
            has_global_summary=False,
            has_tldr=False,
            success=False,
            error_message=error,
        )

        try:
            await self._event_bus.publish(event)
            self._logger.info(
                "ArticleAIProcessedEvent emitido",
                article_id=article_id,
                success=False,
            )
        except Exception as e:
            self._logger.error(
                "Error emitiendo ArticleAIProcessedEvent",
                article_id=article_id,
                error=str(e),
            )

        # Limpiar estado del pipeline
        del self._pipelines[article_id]

    def get_pipeline_state(self, article_id: str) -> Optional[ArticlePipelineState]:
        """
        Obtiene el estado del pipeline para un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            Estado del pipeline o None si no existe
        """
        return self._pipelines.get(article_id)

    def get_active_pipelines_count(self) -> int:
        """
        Obtiene el número de pipelines activos.

        Returns:
            Número de pipelines en progreso
        """
        return sum(
            1
            for p in self._pipelines.values()
            if p.state not in (PipelineState.COMPLETED, PipelineState.FAILED)
        )

    def get_all_pipeline_states(self) -> Dict[str, ArticlePipelineState]:
        """
        Obtiene todos los estados de pipelines activos.

        Returns:
            Diccionario de estados por article_id
        """
        return self._pipelines.copy()
