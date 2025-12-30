"""Handler para PersistChunksCommand."""

from src.chunking.app.commands.persist_chunks.command import PersistChunksCommand
from src.chunking.app.commands.persist_chunks.result import PersistChunksResult
from src.chunking.domain.interfaces.repositories import IContentChunkWriteRepository
from src.chunking.domain.interfaces.services import (
    IChunkValidationService,
    IVectorStore,
)
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork


class PersistChunksHandler:
    """
    Handler para persistir chunks en vector store.

    Responsabilidades:
    - Cargar chunks desde repository
    - Validar chunks antes de persistir
    - Persistir chunks válidos en vector store
    - Marcar chunks como completados (emite ChunkCompletedEvent)
    - Usar UoW para transacción

    NO emite eventos adicionales (ContentChunk.mark_as_completed() ya emite).
    """

    def __init__(
        self,
        chunk_repository: IContentChunkWriteRepository,
        vector_store: IVectorStore,
        validation_service: IChunkValidationService,
        uow: IUnitOfWork,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            chunk_repository: Repository para cargar/persistir chunks
            vector_store: Vector store para persistir embeddings
            validation_service: Service para validar chunks
            uow: Unit of Work para transacciones
            logger: Logger para registrar operaciones
        """
        self._chunk_repository = chunk_repository
        self._vector_store = vector_store
        self._validation_service = validation_service
        self._uow = uow
        self._logger = logger.bind(
            layer="application",
            component="PersistChunksHandler",
        )

    async def handle(
        self,
        command: PersistChunksCommand,
    ) -> PersistChunksResult:
        """
        Ejecuta el comando de persistir chunks.

        Args:
            command: Comando con article_id

        Returns:
            PersistChunksResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando persistencia de chunks",
            article_id=command.article_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Cargar chunks desde repository
            chunks = await self._chunk_repository.find_by_article_id(command.article_id)

            if not chunks:
                self._logger.warning(
                    "No se encontraron chunks para persistir",
                    article_id=command.article_id,
                )
                return PersistChunksResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunks para el artículo",
                )

            # 2. Validar chunks antes de persistir
            # Necesitamos la configuración para validar
            from src.shared.config.chunking_config import ChunkingConfig

            config = ChunkingConfig.from_env()

            validation_errors = (
                self._validation_service.validate_chunks_for_persistence(chunks, config)
            )

            if validation_errors:
                self._logger.error(
                    "Validación de chunks falló",
                    article_id=command.article_id,
                    errors=validation_errors,
                )
                return PersistChunksResult.failure(
                    article_id=command.article_id,
                    error_message=f"Validación falló: {'; '.join(validation_errors)}",
                )

            # Filtrar chunks que ya están completados
            valid_chunks = [chunk for chunk in chunks if not chunk.is_completed()]
            invalid_count = len(chunks) - len(valid_chunks)

            if invalid_count > 0:
                self._logger.warning(
                    "Algunos chunks ya están completados",
                    article_id=command.article_id,
                    already_completed=invalid_count,
                    total_chunks=len(chunks),
                )

            # 3. Usar UoW para transacción
            async with self._uow:
                # 4. Persistir chunks válidos en vector store
                await self._vector_store.store_chunks(valid_chunks)

                self._logger.info(
                    "Chunks persistidos en vector store",
                    article_id=command.article_id,
                    chunks_count=len(valid_chunks),
                )

                # 5. Marcar chunks como completados (emite ChunkCompletedEvent)
                for chunk in valid_chunks:
                    chunk.mark_as_completed()

                # 6. Persistir chunks actualizados en repository
                for chunk in valid_chunks:
                    await self._chunk_repository.save(chunk)

                # 7. Commit transacción
                await self._uow.commit()

            self._logger.info(
                "Persistencia de chunks completada exitosamente",
                article_id=command.article_id,
                chunks_persisted=len(valid_chunks),
                chunks_skipped=invalid_count,
            )

            return PersistChunksResult.success_result(
                article_id=command.article_id,
                chunks_persisted=len(valid_chunks),
                chunks_skipped=invalid_count,
            )

        except Exception as e:
            self._logger.error(
                "Error persistiendo chunks",
                article_id=command.article_id,
                error=str(e),
                exc_info=True,
            )
            return PersistChunksResult.failure(
                article_id=command.article_id,
                error_message=f"Error persistiendo chunks: {str(e)}",
            )
