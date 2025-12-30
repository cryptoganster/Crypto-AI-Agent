"""Handler para GetArticleProcessingStatusQuery."""

from typing import Optional

from src.chunking.app.process_managers.article_ai_processing_pipeline import (
    ArticleAIProcessingPipeline,
)
from src.chunking.app.queries.get_article_processing_status.dto import (
    ArticleProcessingStatusDTO,
)
from src.chunking.app.queries.get_article_processing_status.query import (
    GetArticleProcessingStatusQuery,
)
from src.shared.kernel.logger import ILogger


class GetArticleProcessingStatusHandler:
    """
    Handler para GetArticleProcessingStatusQuery.

    Responsabilidad: Consultar el estado del pipeline de procesamiento
    sin modificar ningún estado.

    Este handler es una query pura (CQRS) que solo lee estado.
    """

    def __init__(
        self,
        pipeline_manager: ArticleAIProcessingPipeline,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            pipeline_manager: Process Manager con el estado del pipeline
            logger: Logger para registrar operaciones
        """
        self._pipeline_manager = pipeline_manager
        self._logger = logger.bind(
            layer="application",
            component="GetArticleProcessingStatusHandler",
        )

    async def handle(
        self, query: GetArticleProcessingStatusQuery
    ) -> Optional[ArticleProcessingStatusDTO]:
        """
        Ejecuta la query para obtener el estado de procesamiento.

        Args:
            query: Query con el article_id

        Returns:
            DTO con el estado actual o None si no hay pipeline activo

        Example:
            >>> query = GetArticleProcessingStatusQuery(article_id="art-123")
            >>> dto = await handler.handle(query)
            >>> if dto:
            ...     print(f"Estado: {dto.state}")
            ...     print(f"Progreso: {dto.progress_percentage:.1f}%")
        """
        self._logger.debug(
            "Consultando estado de procesamiento",
            article_id=query.article_id,
        )

        # Obtener estado del pipeline (NO modifica estado)
        pipeline_state = self._pipeline_manager.get_pipeline_state(query.article_id)

        if pipeline_state is None:
            self._logger.debug(
                "No hay pipeline activo para el artículo",
                article_id=query.article_id,
            )
            return None

        # Convertir estado interno a DTO público
        dto = ArticleProcessingStatusDTO(
            article_id=pipeline_state.article_id,
            state=pipeline_state.state.value,
            total_chunks=pipeline_state.metrics.total_chunks,
            chunks_created=pipeline_state.metrics.chunks_created,
            chunks_embedded=pipeline_state.metrics.chunks_embedded,
            chunks_summarized=pipeline_state.metrics.chunks_summarized,
            chunks_completed=pipeline_state.metrics.chunks_completed,
            chunks_failed=pipeline_state.metrics.chunks_failed,
            started_at=pipeline_state.metrics.started_at,
            completed_at=pipeline_state.metrics.completed_at,
            duration_seconds=pipeline_state.metrics.duration_seconds,
            error_message=pipeline_state.error_message,
            enable_global_summary=pipeline_state.enable_global_summary,
            enable_tldr=pipeline_state.enable_tldr,
        )

        self._logger.debug(
            "Estado de procesamiento obtenido",
            article_id=query.article_id,
            state=dto.state,
            progress=f"{dto.progress_percentage:.1f}%",
        )

        return dto
