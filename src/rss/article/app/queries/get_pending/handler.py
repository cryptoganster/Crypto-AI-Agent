"""Handler para GetPendingArticlesQuery."""

from src.rss.article.domain.interfaces.repositories import IArticleReadRepository
from src.shared.kernel.logger import ILogger

from .query import GetPendingArticlesQuery
from .result import GetPendingArticlesResult, PendingArticleDTO


class GetPendingArticlesHandler:
    """
    Handler para GetPendingArticlesQuery (CQRS Read Side).

    Responsabilidades:
    - Obtener artículos pendientes desde ReadRepository
    - Mapear a DTO ligero
    - Retornar Result Object

    CQRS Estricto:
    - Solo lectura (no modifica estado)
    - Usa ReadRepository
    - Retorna DTOs sin comportamiento
    """

    def __init__(
        self,
        read_repository: IArticleReadRepository,
        logger: ILogger,
    ):
        """
        Inicializa handler.

        Args:
            read_repository: Repository de lectura (CQRS read side)
            logger: Logger para observabilidad
        """
        self._read_repo = read_repository
        self._logger = logger.bind(
            layer="application",
            component="GetPendingArticlesHandler",
        )

    async def handle(self, query: GetPendingArticlesQuery) -> GetPendingArticlesResult:
        """
        Ejecuta query de lectura.

        Args:
            query: Query con limit opcional

        Returns:
            GetPendingArticlesResult con lista de PendingArticleDTO
        """
        self._logger.debug(
            "Ejecutando GetPendingArticlesQuery",
            limit=query.limit,
        )

        try:
            # Leer desde ReadRepository
            articles_data = await self._read_repo.find_pending_processing(
                limit=query.limit
            )

            if not articles_data:
                self._logger.debug("No hay artículos pendientes")
                return GetPendingArticlesResult.empty_result()

            # Mapear a DTOs ligeros
            dtos = [
                PendingArticleDTO(
                    id=article.id,
                    source_id=article.source_id,
                    title=article.title,
                    url=article.url,
                    has_scraped_content=article.content_scraped is not None,
                    has_plaintext_content=article.content_plaintext is not None,
                    has_markdown_content=article.content_markdown is not None,
                    created_at=article.created_at,
                    updated_at=article.updated_at,
                )
                for article in articles_data
            ]

            self._logger.info(
                "Artículos pendientes obtenidos",
                count=len(dtos),
            )

            return GetPendingArticlesResult.success_result(dtos)

        except Exception as e:
            self._logger.exception(
                "Error ejecutando GetPendingArticlesQuery",
                error=str(e),
            )
            return GetPendingArticlesResult.failure(str(e))
