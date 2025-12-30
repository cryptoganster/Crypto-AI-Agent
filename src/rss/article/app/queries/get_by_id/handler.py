"""Handler para GetArticleByIdQuery."""

from uuid import UUID

from src.rss.article.domain.interfaces.repositories import IArticleReadRepository
from src.shared.kernel.logger import ILogger

from .query import GetArticleByIdQuery
from .result import ArticleDTO, GetArticleByIdResult


class GetArticleByIdHandler:
    """
    Handler para GetArticleByIdQuery (CQRS Read Side).

    Responsabilidades:
    - Obtener artículo desde ReadRepository
    - Mapear a DTO específico de esta query
    - Retornar Result Object

    CQRS Estricto:
    - Solo lectura (no modifica estado)
    - Usa ReadRepository (devuelve datos planos)
    - Retorna DTO sin comportamiento
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
            component="GetArticleByIdHandler",
        )

    async def handle(self, query: GetArticleByIdQuery) -> GetArticleByIdResult:
        """
        Ejecuta query de lectura.

        Args:
            query: Query con article_id

        Returns:
            GetArticleByIdResult con ArticleDTO o error
        """
        self._logger.debug(
            "Ejecutando GetArticleByIdQuery",
            article_id=str(query.article_id),
        )

        try:
            # Leer desde ReadRepository (devuelve datos planos)
            article_data = await self._read_repo.find_by_id(query.article_id)

            if not article_data:
                self._logger.debug(
                    "Artículo no encontrado",
                    article_id=str(query.article_id),
                )
                return GetArticleByIdResult.not_found(query.article_id)

            # Mapear a DTO específico de esta query
            dto = ArticleDTO(
                id=article_data.id,
                source_id=article_data.source_id,
                title=article_data.title,
                url=article_data.url,
                summary=article_data.summary,
                author=article_data.author,
                language=article_data.language,
                thumbnail_url=article_data.thumbnail_url,
                content_scraped=article_data.content_scraped,
                content_plaintext=article_data.content_plaintext,
                content_markdown=article_data.content_markdown,
                content_excerpt=article_data.content_excerpt,
                keywords=article_data.keywords,
                categories=article_data.categories,
                word_count=article_data.word_count,
                reading_time_minutes=article_data.reading_time_minutes,
                quality_score=article_data.quality_score,
                published_at=article_data.published_at,
                created_at=article_data.created_at,
                updated_at=article_data.updated_at,
            )

            self._logger.debug(
                "Artículo obtenido exitosamente",
                article_id=str(query.article_id),
            )

            return GetArticleByIdResult.success_result(dto)

        except Exception as e:
            self._logger.exception(
                "Error ejecutando GetArticleByIdQuery",
                article_id=str(query.article_id),
                error=str(e),
            )
            return GetArticleByIdResult.failure(str(e))
