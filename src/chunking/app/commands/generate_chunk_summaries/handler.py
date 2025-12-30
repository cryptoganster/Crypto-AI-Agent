"""Handler para GenerateChunkSummariesCommand."""

from typing import List

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.repositories.content_chunk_read_repository import (
    IContentChunkReadRepository,
)
from src.chunking.domain.interfaces.repositories.content_chunk_write_repository import (
    IContentChunkWriteRepository,
)
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.rag.domain.interfaces.services.summarization_service import (
    ISummarizationService,
)
from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.kernel.logger import ILogger

from .command import GenerateChunkSummariesCommand
from .result import GenerateChunkSummariesResult


class GenerateChunkSummariesHandler:
    """
    Handler para generar summaries de chunks.

    Responsabilidades:
    - Cargar chunks desde repository
    - Generar summaries individuales usando ISummarizationService
    - Llamar chunk.summarize() para cada chunk (emite ChunkSummarizedEvent)
    - Persistir chunks actualizados
    - NO emitir eventos adicionales (ContentChunk ya emite)

    Flujo:
    1. Cargar chunks del artículo desde repository
    2. Filtrar chunks que necesitan summary (summary=None)
    3. Para cada chunk:
       a. Generar summary usando ISummarizationService.summarize_chunk()
       b. Llamar chunk.summarize(summary)
       c. Persistir chunk actualizado
    4. Retornar resultado con número de chunks summarizados

    Examples:
        >>> handler = GenerateChunkSummariesHandler(
        ...     summarization_service=summarization_service,
        ...     chunk_read_repository=chunk_read_repo,
        ...     chunk_write_repository=chunk_write_repo,
        ...     config=ai_config,
        ...     logger=logger
        ... )
        >>> command = GenerateChunkSummariesCommand(article_id="art-123")
        >>> result = await handler.handle(command)
        >>> result.success
        True
        >>> result.chunks_summarized
        10
    """

    def __init__(
        self,
        summarization_service: ISummarizationService,
        chunk_read_repository: IContentChunkReadRepository,
        chunk_write_repository: IContentChunkWriteRepository,
        config: AIProcessingConfig,
        logger: ILogger,
    ):
        """
        Inicializa handler.

        Args:
            summarization_service: Servicio para generar summaries
            chunk_read_repository: Repository para leer chunks
            chunk_write_repository: Repository para persistir chunks
            config: Configuración de procesamiento AI
            logger: Logger para tracking
        """
        self._summarization_service = summarization_service
        self._chunk_read_repository = chunk_read_repository
        self._chunk_write_repository = chunk_write_repository
        self._config = config
        self._logger = logger.bind(
            layer="application",
            component="GenerateChunkSummariesHandler",
        )

    async def handle(
        self,
        command: GenerateChunkSummariesCommand,
    ) -> GenerateChunkSummariesResult:
        """
        Ejecuta comando de generación de summaries.

        Args:
            command: Comando con article_id

        Returns:
            GenerateChunkSummariesResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando generación de summaries",
            article_id=command.article_id,
            correlation_id=command.correlation_id,
            triggered_by=command.triggered_by,
        )

        try:
            # 1. Cargar chunks del artículo
            chunks = await self._chunk_read_repository.find_by_article_id(
                command.article_id
            )

            if not chunks:
                self._logger.warning(
                    "No se encontraron chunks para el artículo",
                    article_id=command.article_id,
                )
                return GenerateChunkSummariesResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunks para el artículo",
                )

            # 2. Filtrar chunks que necesitan summary (status=EMBEDDED)
            pending_chunks = [
                chunk
                for chunk in chunks
                if chunk.status == ChunkStatus.EMBEDDED and chunk.summary is None
            ]

            if not pending_chunks:
                self._logger.info(
                    "Todos los chunks ya tienen summaries",
                    article_id=command.article_id,
                    total_chunks=len(chunks),
                )
                return GenerateChunkSummariesResult.success_result(
                    article_id=command.article_id,
                    chunks_summarized=0,
                    total_chunks=len(chunks),
                )

            self._logger.info(
                "Chunks pendientes de summarization encontrados",
                article_id=command.article_id,
                pending_chunks=len(pending_chunks),
                total_chunks=len(chunks),
            )

            # 3. Procesar chunks individualmente
            chunks_summarized = await self._process_chunks(
                pending_chunks,
                command.article_id,
            )

            self._logger.info(
                "Generación de summaries completada",
                article_id=command.article_id,
                chunks_summarized=chunks_summarized,
                total_chunks=len(chunks),
            )

            return GenerateChunkSummariesResult.success_result(
                article_id=command.article_id,
                chunks_summarized=chunks_summarized,
                total_chunks=len(chunks),
            )

        except Exception as e:
            self._logger.error(
                "Error generando summaries",
                article_id=command.article_id,
                error=str(e),
                exc_info=True,
            )
            return GenerateChunkSummariesResult.failure(
                article_id=command.article_id,
                error_message=f"Error generando summaries: {str(e)}",
            )

    async def _process_chunks(
        self,
        chunks: List[ContentChunk],
        article_id: str,
    ) -> int:
        """
        Procesa chunks para generar summaries.

        Args:
            chunks: Lista de chunks a procesar
            article_id: ID del artículo (para logging)

        Returns:
            Número de chunks summarizados exitosamente
        """
        chunks_summarized = 0
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks, 1):
            self._logger.debug(
                "Generando summary para chunk",
                article_id=article_id,
                chunk_id=str(chunk.id),
                chunk_num=idx,
                total_chunks=total_chunks,
            )

            try:
                # Generar summary usando servicio (retorna texto)
                summary_text = await self._summarization_service.summarize_chunk(
                    chunk.content
                )

                # Crear ChunkSummary value object desde texto
                chunk_summary = ChunkSummary.from_text(summary_text)

                # Llamar chunk.summarize() - emite ChunkSummarizedEvent automáticamente
                chunk.summarize(chunk_summary)
                chunks_summarized += 1

                # Persistir chunk actualizado
                await self._chunk_write_repository.save(chunk)

                self._logger.debug(
                    "Summary generado exitosamente",
                    article_id=article_id,
                    chunk_id=str(chunk.id),
                    summary_length=len(chunk_summary.content),
                    sentence_count=chunk_summary.sentence_count,
                )

            except ValueError as e:
                self._logger.warning(
                    "Error aplicando summary a chunk",
                    chunk_id=str(chunk.id),
                    article_id=article_id,
                    error=str(e),
                )
                continue

            except Exception as e:
                self._logger.error(
                    "Error generando summary para chunk",
                    article_id=article_id,
                    chunk_id=str(chunk.id),
                    chunk_num=idx,
                    error=str(e),
                    exc_info=True,
                )
                # Continuar con siguiente chunk
                continue

        return chunks_summarized
