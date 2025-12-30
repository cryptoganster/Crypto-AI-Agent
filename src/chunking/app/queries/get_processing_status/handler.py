"""Handler para GetProcessingStatus query."""

from src.chunking.app.queries.get_processing_status.dto import (
    ProcessingStatusDTO,
)
from src.chunking.app.queries.get_processing_status.query import (
    GetProcessingStatusQuery,
)
from src.chunking.domain.interfaces.processing_status_repository import (
    IProcessingStatusRepository,
)
from src.shared.kernel.logger import ILogger


class GetProcessingStatusHandler:
    """
    Handler para obtener estado de procesamiento de artículo.

    Flujo:
    1. Buscar estado en repository
    2. Retornar status, chunks_created, total_tokens

    Validates: Requirements 10.7
    """

    def __init__(
        self,
        processing_status_repository: IProcessingStatusRepository,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            processing_status_repository: Repository para leer estado
            logger: Logger para registrar operaciones
        """
        self._repository = processing_status_repository
        self._logger = logger.bind(
            layer="application",
            component="GetProcessingStatusHandler",
        )

    async def handle(
        self,
        query: GetProcessingStatusQuery,
    ) -> ProcessingStatusDTO | None:
        """
        Ejecuta query para obtener estado de procesamiento.

        Args:
            query: Query con article_id

        Returns:
            ProcessingStatusDTO si existe, None si no se ha procesado

        Raises:
            Exception: Si la recuperación falla
        """
        self._logger.info(
            "Obteniendo estado de procesamiento",
            article_id=query.article_id,
        )

        try:
            # Buscar estado en repository
            status = await self._repository.find_by_article_id(query.article_id)

            if status is None:
                self._logger.info(
                    "No se encontró estado de procesamiento",
                    article_id=query.article_id,
                )
                return None

            # Convertir a DTO
            status_dto = ProcessingStatusDTO(
                article_id=status.article_id,
                status=status.status,
                total_chunks=status.total_chunks,
                chunks_embedded=status.chunks_embedded,
                chunks_summarized=status.chunks_summarized,
                chunks_completed=status.chunks_completed,
                has_global_summary=status.has_global_summary,
                has_tldr=status.has_tldr,
                cluster_id=status.cluster_id,
                started_at=status.started_at,
                completed_at=status.completed_at,
                progress_percentage=status.progress_percentage,
                is_completed=status.is_completed,
            )

            self._logger.info(
                "Estado de procesamiento recuperado",
                article_id=query.article_id,
                status=status.status,
                progress=f"{status.progress_percentage:.1f}%",
            )

            return status_dto

        except Exception as e:
            self._logger.error(
                "Error obteniendo estado de procesamiento",
                error=str(e),
                article_id=query.article_id,
            )
            raise
