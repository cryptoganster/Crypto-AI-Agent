"""Handler para GenerateGlobalSummaryCommand."""

from src.chunking.app.commands.generate_global_summary.command import (
    GenerateGlobalSummaryCommand,
)
from src.chunking.app.commands.generate_global_summary.result import (
    GenerateGlobalSummaryResult,
)
from src.chunking.domain.interfaces.repositories import IContentChunkReadRepository
from src.rag.domain.interfaces.services import ISummarizationService
from src.rss.article.domain.interfaces.repositories import IArticleWriteRepository
from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.kernel.logger import ILogger


class GenerateGlobalSummaryHandler:
    """
    Handler para generar summary global de un artículo.

    Responsabilidades:
    - Cargar chunks desde repository
    - Extraer chunk summaries
    - Generar summary global usando ISummarizationService
    - Limitar texto según configuración
    - Actualizar Article aggregate con global_summary
    - Persistir Article actualizado

    NO emite eventos adicionales (Process Manager detecta completitud).
    """

    def __init__(
        self,
        summarization_service: ISummarizationService,
        chunk_repository: IContentChunkReadRepository,
        article_repository: IArticleWriteRepository,
        config: AIProcessingConfig,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            summarization_service: Service para generar summaries
            chunk_repository: Repository para cargar chunks
            article_repository: Repository para cargar/persistir artículos
            config: Configuración de procesamiento AI
            logger: Logger para registrar operaciones
        """
        self._summarization_service = summarization_service
        self._chunk_repository = chunk_repository
        self._article_repository = article_repository
        self._config = config
        self._logger = logger.bind(
            layer="application",
            component="GenerateGlobalSummaryHandler",
        )

    async def handle(
        self,
        command: GenerateGlobalSummaryCommand,
    ) -> GenerateGlobalSummaryResult:
        """
        Ejecuta el comando de generar summary global.

        Args:
            command: Comando con article_id

        Returns:
            GenerateGlobalSummaryResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando generación de summary global",
            article_id=command.article_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Cargar chunks desde repository
            chunks = await self._chunk_repository.find_by_article_id(command.article_id)

            if not chunks:
                self._logger.warning(
                    "No se encontraron chunks para generar summary global",
                    article_id=command.article_id,
                )
                return GenerateGlobalSummaryResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunks para el artículo",
                )

            # 2. Extraer chunk summaries
            chunk_summaries = []
            for chunk in chunks:
                if chunk.summary and chunk.summary.content:
                    chunk_summaries.append(chunk.summary.content)

            if not chunk_summaries:
                self._logger.warning(
                    "No se encontraron chunk summaries para generar summary global",
                    article_id=command.article_id,
                    total_chunks=len(chunks),
                )
                return GenerateGlobalSummaryResult.failure(
                    article_id=command.article_id,
                    error_message="No se encontraron chunk summaries",
                )

            # 3. Cargar artículo para obtener título
            article = await self._article_repository.find_by_id(command.article_id)

            if not article:
                self._logger.error(
                    "Artículo no encontrado",
                    article_id=command.article_id,
                )
                return GenerateGlobalSummaryResult.failure(
                    article_id=command.article_id,
                    error_message="Artículo no encontrado",
                )

            # 4. Generar summary global usando service
            max_length = self._config.global_summary_max_length

            self._logger.info(
                "Generando summary global",
                article_id=command.article_id,
                chunks_used=len(chunk_summaries),
                max_length=max_length,
            )

            global_summary = self._summarization_service.generate_global_summary(
                chunk_summaries=chunk_summaries,
                article_title=str(article._metadata.title),
                max_length=max_length,
            )

            # 5. Validar calidad del summary
            is_valid = self._summarization_service.validate_summary_quality(
                summary=global_summary,
                min_length=50,
                max_length=max_length,
            )

            if not is_valid:
                self._logger.warning(
                    "Summary global generado no cumple criterios de calidad",
                    article_id=command.article_id,
                    summary_length=len(global_summary),
                )
                return GenerateGlobalSummaryResult.failure(
                    article_id=command.article_id,
                    error_message="Summary generado no cumple criterios de calidad",
                )

            # 6. Actualizar Article aggregate con global_summary
            from src.rss.article.domain.value_objects.metadata import ArticleSummary

            article_summary = ArticleSummary(global_summary)
            article.update_summary(article_summary)

            # 7. Persistir Article actualizado
            await self._article_repository.save(article)

            self._logger.info(
                "Summary global generado y persistido exitosamente",
                article_id=command.article_id,
                summary_length=len(global_summary),
                chunks_used=len(chunk_summaries),
            )

            return GenerateGlobalSummaryResult.success_result(
                article_id=command.article_id,
                global_summary=global_summary,
                chunks_used=len(chunk_summaries),
            )

        except ValueError as e:
            self._logger.error(
                "Error de validación generando summary global",
                article_id=command.article_id,
                error=str(e),
            )
            return GenerateGlobalSummaryResult.failure(
                article_id=command.article_id,
                error_message=f"Error de validación: {str(e)}",
            )
        except Exception as e:
            self._logger.error(
                "Error generando summary global",
                article_id=command.article_id,
                error=str(e),
                exc_info=True,
            )
            return GenerateGlobalSummaryResult.failure(
                article_id=command.article_id,
                error_message=f"Error generando summary global: {str(e)}",
            )
