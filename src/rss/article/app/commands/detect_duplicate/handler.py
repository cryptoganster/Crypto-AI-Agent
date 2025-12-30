"""Handler para DetectDuplicateArticle command."""

from src.rss.article.app.commands.detect_duplicate.command import (
    DetectDuplicateArticleCommand,
)
from src.rss.article.app.commands.detect_duplicate.result import (
    DetectDuplicateArticleResult,
)
from src.rss.article.domain.services import SemanticDeduplicationService
from src.shared.kernel.logger import ILogger


class DetectDuplicateArticleHandler:
    """
    Handler para detectar artículos duplicados usando embeddings.

    Responsabilidades:
    - Usar SemanticDeduplicationService para buscar duplicados
    - Loggear resultados de detección
    - Retornar lista de duplicados encontrados

    NOTA: Este handler NO modifica estado (es read-only).
    NO necesita UoW ni WriteRepository.
    """

    def __init__(
        self,
        deduplication_service: SemanticDeduplicationService,
        logger: ILogger,
    ):
        """
        Inicializa handler.

        Args:
            deduplication_service: Servicio de deduplicación semántica
            logger: Logger para tracking
        """
        self._deduplication_service = deduplication_service
        self._logger = logger.bind(
            layer="application",
            handler="DetectDuplicateArticleHandler",
        )

    async def handle(
        self,
        command: DetectDuplicateArticleCommand,
    ) -> DetectDuplicateArticleResult:
        """
        Ejecuta detección de duplicados.

        Args:
            command: Comando con article_id a verificar

        Returns:
            Result con lista de duplicados encontrados
        """
        self._logger.info(
            "Detectando duplicados semánticos",
            article_id=command.article_id,
            max_results=command.max_results,
        )

        try:
            # Buscar duplicados usando servicio de dominio
            duplicates = await self._deduplication_service.find_duplicates(
                article_id=command.article_id,
                max_results=command.max_results,
            )

            if duplicates:
                self._logger.warning(
                    "Duplicados detectados",
                    article_id=command.article_id,
                    count=len(duplicates),
                    top_match=duplicates[0].article_id,
                    top_score=duplicates[0].similarity_score,
                )
            else:
                self._logger.info(
                    "No se encontraron duplicados",
                    article_id=command.article_id,
                )

            return DetectDuplicateArticleResult.success_result(
                article_id=command.article_id,
                duplicates=duplicates,
            )

        except ValueError as e:
            # Artículo no tiene embedding
            self._logger.warning(
                "No se pudo detectar duplicados",
                article_id=command.article_id,
                error=str(e),
            )
            return DetectDuplicateArticleResult.failure(
                article_id=command.article_id,
                error=str(e),
            )

        except Exception as e:
            self._logger.error(
                "Error detectando duplicados",
                article_id=command.article_id,
                error=str(e),
            )
            return DetectDuplicateArticleResult.failure(
                article_id=command.article_id,
                error=f"Error inesperado: {str(e)}",
            )
