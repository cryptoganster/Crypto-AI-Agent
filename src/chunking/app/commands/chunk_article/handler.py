"""Handler para ChunkArticleCommand."""

from datetime import datetime
from typing import List

from src.chunking.app.commands.chunk_article.command import ChunkArticleCommand
from src.chunking.app.commands.chunk_article.result import ChunkArticleResult
from src.chunking.domain.aggregates import KnowledgeChunk
from src.chunking.domain.interfaces.repositories.content_chunk_write_repository import (
    IContentChunkWriteRepository,
)
from src.chunking.domain.interfaces.services.chunking_service import IChunkingService
from src.knowledge.domain.value_objects.source_reference import SourceReference
from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork


class ChunkArticleHandler:
    """
    Handler para ChunkArticleCommand.

    Responsabilidad única: Dividir artículo en chunks y persistirlos.

    Flujo:
    1. Validar comando
    2. Usar IChunkingService para dividir texto en chunks
    3. Crear ContentChunk aggregates (emiten ChunkCreatedEvent automáticamente)
    4. Persistir chunks usando repository
    5. Commit via UoW
    6. Retornar resultado

    NO emite eventos adicionales - ContentChunk ya emite ChunkCreatedEvent
    en su constructor cuando status=PENDING.

    Attributes:
        _chunking_service: Servicio de chunking
        _chunk_repository: Repository para persistir chunks
        _uow: Unit of Work para transacciones
        _config: Configuración de procesamiento AI
        _logger: Logger
    """

    def __init__(
        self,
        chunking_service: IChunkingService,
        chunk_repository: IContentChunkWriteRepository,
        uow: IUnitOfWork,
        config: AIProcessingConfig,
        logger: ILogger,
    ):
        """
        Inicializa ChunkArticleHandler.

        Args:
            chunking_service: Servicio de chunking
            chunk_repository: Repository para persistir chunks
            uow: Unit of Work para transacciones
            config: Configuración de procesamiento AI
            logger: Logger
        """
        self._chunking_service = chunking_service
        self._chunk_repository = chunk_repository
        self._uow = uow
        self._config = config
        self._logger = logger.bind(
            layer="application",
            component="ChunkArticleHandler",
        )

    async def handle(self, command: ChunkArticleCommand) -> ChunkArticleResult:
        """
        Ejecuta ChunkArticleCommand.

        Args:
            command: Comando a ejecutar

        Returns:
            ChunkArticleResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando chunking de artículo",
            article_id=command.article_id,
            source_type=command.source_type,
            text_length=len(command.text),
            correlation_id=command.correlation_id,
        )

        # 1. Validar comando
        validation_error = self._validate_command(command)
        if validation_error:
            self._logger.warning(
                "Validación de comando falló",
                article_id=command.article_id,
                error=validation_error,
            )
            return ChunkArticleResult.failure(
                article_id=command.article_id,
                source_type=command.source_type,
                error_message=validation_error,
            )

        try:
            # 2. Parsear published_at si existe
            published_at = None
            if command.published_at:
                try:
                    published_at = datetime.fromisoformat(
                        command.published_at.replace("Z", "+00:00")
                    )
                except ValueError as e:
                    self._logger.warning(
                        "Error parseando published_at, continuando sin fecha",
                        article_id=command.article_id,
                        published_at=command.published_at,
                        error=str(e),
                    )

            # 3. Crear SourceReference
            source = SourceReference(
                source_id=command.article_id,
                source_type=command.source_type,
                source_url=command.source_url,
            )

            # 4. Usar IChunkingService para dividir texto
            chunks: List[KnowledgeChunk] = self._chunking_service.chunk_text(
                text=command.text,
                source=source,
                published_at=published_at,
                topics=command.topics,
            )

            self._logger.info(
                "Chunks creados exitosamente",
                article_id=command.article_id,
                source_type=command.source_type,
                chunks_count=len(chunks),
            )

            # 5. Persistir chunks usando UoW
            async with self._uow:
                for chunk in chunks:
                    await self._chunk_repository.save(chunk)

                # Commit explícito
                await self._uow.commit()

            self._logger.info(
                "Chunks persistidos exitosamente",
                article_id=command.article_id,
                source_type=command.source_type,
                chunks_count=len(chunks),
            )

            # 6. Retornar resultado exitoso
            return ChunkArticleResult.success(
                article_id=command.article_id,
                source_type=command.source_type,
                chunks_created=len(chunks),
            )

        except Exception as e:
            self._logger.error(
                "Error ejecutando ChunkArticleCommand",
                article_id=command.article_id,
                source_type=command.source_type,
                error=str(e),
                exc_info=True,
            )
            return ChunkArticleResult.failure(
                article_id=command.article_id,
                source_type=command.source_type,
                error_message=f"Error chunking article: {str(e)}",
            )

    def _validate_command(self, command: ChunkArticleCommand) -> str | None:
        """
        Valida comando.

        Args:
            command: Comando a validar

        Returns:
            Mensaje de error si inválido, None si válido
        """
        if not command.article_id or not command.article_id.strip():
            return "article_id es requerido"

        if not command.text or not command.text.strip():
            return "text es requerido y no puede estar vacío"

        if not command.source_url or not command.source_url.startswith(
            ("http://", "https://")
        ):
            return "source_url debe ser una URL válida"

        if not command.source_type or not command.source_type.strip():
            return "source_type es requerido"

        # Validar source_type permitidos
        valid_types = ["rss_article", "web_scrape", "manual_entry", "api_import"]
        if command.source_type not in valid_types:
            return f"source_type debe ser uno de: {', '.join(valid_types)}"

        # Validar longitud mínima del texto
        if len(command.text.strip()) < 100:
            return "text debe tener al menos 100 caracteres"

        return None
