"""Handler para GenerateChunkEmbeddingsCommand."""

from typing import List

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.repositories.content_chunk_read_repository import (
    IContentChunkReadRepository,
)
from src.chunking.domain.interfaces.repositories.content_chunk_write_repository import (
    IContentChunkWriteRepository,
)
from src.chunking.domain.interfaces.services.embedding_service import IEmbeddingService
from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.kernel.logger import ILogger

from .command import GenerateChunkEmbeddingsCommand
from .result import GenerateChunkEmbeddingsResult


class GenerateChunkEmbeddingsHandler:
    """
    Handler para generar embeddings de chunks.

    Responsabilidades:
    - Cargar chunks desde repository
    - Generar embeddings en batches usando IEmbeddingService
    - Llamar chunk.embed() para cada chunk (emite ChunkEmbeddedEvent)
    - Persistir chunks actualizados
    - NO emitir eventos adicionales (ContentChunk ya emite)

    Flujo:
    1. Cargar chunks del artículo desde repository
    2. Filtrar chunks que necesitan embedding (status=PENDING)
    3. Procesar en batches según configuración
    4. Para cada batch:
       a. Generar embeddings usando IEmbeddingService.embed_batch()
       b. Llamar chunk.embed(embedding) para cada chunk
       c. Persistir chunks actualizados
    5. Retornar resultado con número de chunks procesados

    Examples:
        >>> handler = GenerateChunkEmbeddingsHandler(
        ...     embedding_service=ollama_adapter,
        ...     chunk_repository=chunk_repo,
        ...     config=ai_config,
        ...     logger=logger
        ... )
        >>> command = GenerateChunkEmbeddingsCommand(article_id="art-123")
        >>> result = await handler.handle(command)
        >>> result.success
        True
        >>> result.chunks_processed
        10
    """

    def __init__(
        self,
        embedding_service: IEmbeddingService,
        chunk_read_repository: IContentChunkReadRepository,
        chunk_write_repository: IContentChunkWriteRepository,
        config: AIProcessingConfig,
        logger: ILogger,
    ):
        """
        Inicializa handler.

        Args:
            embedding_service: Servicio para generar embeddings
            chunk_read_repository: Repository para leer chunks
            chunk_write_repository: Repository para persistir chunks
            config: Configuración de procesamiento AI
            logger: Logger para tracking
        """
        self._embedding_service = embedding_service
        self._chunk_read_repository = chunk_read_repository
        self._chunk_write_repository = chunk_write_repository
        self._config = config
        self._logger = logger.bind(
            layer="application",
            component="GenerateChunkEmbeddingsHandler",
        )

    async def handle(
        self,
        command: GenerateChunkEmbeddingsCommand,
    ) -> GenerateChunkEmbeddingsResult:
        """
        Ejecuta comando de generación de embeddings.

        Args:
            command: Comando con article_id

        Returns:
            GenerateChunkEmbeddingsResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando generación de embeddings",
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
                return GenerateChunkEmbeddingsResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunks para el artículo",
                )

            # 2. Filtrar chunks que necesitan embedding (status=PENDING)
            pending_chunks = [chunk for chunk in chunks if chunk.embedding is None]

            if not pending_chunks:
                self._logger.info(
                    "Todos los chunks ya tienen embeddings",
                    article_id=command.article_id,
                    total_chunks=len(chunks),
                )
                return GenerateChunkEmbeddingsResult.success_result(
                    article_id=command.article_id,
                    chunks_processed=0,
                )

            self._logger.info(
                "Chunks pendientes de embedding encontrados",
                article_id=command.article_id,
                pending_chunks=len(pending_chunks),
                total_chunks=len(chunks),
            )

            # 3. Procesar en batches
            chunks_processed = await self._process_chunks_in_batches(
                pending_chunks,
                command.article_id,
            )

            self._logger.info(
                "Generación de embeddings completada",
                article_id=command.article_id,
                chunks_processed=chunks_processed,
            )

            return GenerateChunkEmbeddingsResult.success_result(
                article_id=command.article_id,
                chunks_processed=chunks_processed,
            )

        except Exception as e:
            self._logger.error(
                "Error generando embeddings",
                article_id=command.article_id,
                error=str(e),
                exc_info=True,
            )
            return GenerateChunkEmbeddingsResult.failure(
                article_id=command.article_id,
                error_message=f"Error generando embeddings: {str(e)}",
            )

    async def _process_chunks_in_batches(
        self,
        chunks: List[ContentChunk],
        article_id: str,
    ) -> int:
        """
        Procesa chunks en batches para generar embeddings.

        Args:
            chunks: Lista de chunks a procesar
            article_id: ID del artículo (para logging)

        Returns:
            Número de chunks procesados exitosamente
        """
        # Usar batch_size de 32 (estándar para embeddings según Requirements 11.1)
        batch_size = 32
        chunks_processed = 0

        # Dividir en batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(chunks) + batch_size - 1) // batch_size

            self._logger.debug(
                "Procesando batch de embeddings",
                article_id=article_id,
                batch_num=batch_num,
                total_batches=total_batches,
                batch_size=len(batch),
            )

            try:
                # Generar embeddings para el batch
                texts = [chunk.content for chunk in batch]
                embeddings = await self._embedding_service.embed_batch(texts)

                # Aplicar embeddings a chunks
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        # Llamar chunk.embed() - emite ChunkEmbeddedEvent automáticamente
                        chunk.embed(embedding)
                        chunks_processed += 1

                    except ValueError as e:
                        self._logger.warning(
                            "Error aplicando embedding a chunk",
                            chunk_id=str(chunk.id),
                            article_id=article_id,
                            error=str(e),
                        )
                        continue

                # Persistir chunks actualizados del batch
                for chunk in batch:
                    if chunk.embedding is not None:
                        await self._chunk_write_repository.save(chunk)

                self._logger.debug(
                    "Batch de embeddings completado",
                    article_id=article_id,
                    batch_num=batch_num,
                    chunks_in_batch=len(batch),
                    chunks_processed_in_batch=len(
                        [c for c in batch if c.embedding is not None]
                    ),
                )

            except Exception as e:
                self._logger.error(
                    "Error procesando batch de embeddings",
                    article_id=article_id,
                    batch_num=batch_num,
                    error=str(e),
                    exc_info=True,
                )
                # Continuar con siguiente batch
                continue

        return chunks_processed
