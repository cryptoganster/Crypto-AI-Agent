"""Handler para CalculateArticleQuality command - Application Layer."""

from typing import Optional
from uuid import UUID

from src.rss.article.domain.events import ArticleQualityCalculated
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services.quality import (
    IArticleQualityService,
)
from src.shared.domain.value_objects import Level
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import CalculateArticleQualityCommand
from .interface import ICalculateArticleQualityHandler
from .result import CalculateArticleQualityResult


class CalculateArticleQualityHandler(ICalculateArticleQualityHandler):
    """
    Handler para calcular quality completo (score + level) de un artículo RSS.

    Application Layer - coordina operación usando:
    - IArticleQualityService (domain service para cálculo)
    - IArticleWriteRepository (persistencia)

    CQRS ESTRICTO:
    - Solo usa WriteRepository para persistir cambios
    - Datos vienen del evento anterior

    UNIT OF WORK:
    - Usa UoW para manejar transacciones
    - Commit explícito después de save
    - Eventos publicados FUERA de transacción

    Dependency Inversion: Depende de interfaces, no implementaciones.
    """

    def __init__(
        self,
        session_factory,  # Callable[[], AsyncSession]
        quality_service: Optional[IArticleQualityService],
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        """
        Inicializa handler con dependencias inyectadas.

        Args:
            session_factory: Factory para crear nuevas sesiones
            quality_service: Service para calcular quality score
            event_bus: Event bus para publicar eventos de dominio
            logger: Logger para observabilidad
        """
        self._session_factory = session_factory
        self._quality_service = quality_service
        self._event_bus = event_bus
        self._logger = logger

    async def handle(
        self, command: CalculateArticleQualityCommand
    ) -> CalculateArticleQualityResult:
        """
        Calcula quality completo (score + level) del artículo.

        Args:
            command: Comando con article_id

        Returns:
            CalculateArticleQualityResult con score y level o error
        """
        try:
            # 1. Cargar artículo usando WriteRepository (CQRS estricto)
            # Crear sesión temporal para lectura inicial
            from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
                RssArticleWriteRepository,
            )

            read_session = self._session_factory()
            read_repository = RssArticleWriteRepository(
                session=read_session, logger=self._logger
            )

            article_uuid = UUID(command.article_id)
            article = await read_repository.load(article_uuid)

            if not article:
                self._logger.warning(
                    "Article no encontrado para calcular quality",
                    article_id=str(article_uuid),
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleQualityCalculated(
                        article_id=command.article_id,
                        success=False,
                        error_message="Artículo no encontrado",
                    )
                )

                return CalculateArticleQualityResult.failure_result(
                    article_id=command.article_id,
                    message="Artículo no encontrado",
                    error_code="ARTICLE_NOT_FOUND",
                )

            # 2. Verificar si ya tiene quality (a menos que force_recalculate)
            if (
                article.quality.quality_level is not None
                and not command.force_recalculate
            ):
                # Derivar score desde quality_level
                quality_score = article.quality.quality_level.score

                self._logger.debug(
                    "Article ya tiene quality calculado",
                    article_id=str(article_uuid),
                    quality_score=quality_score,
                    quality_level=str(article.quality.quality_level),
                )

                # Emitir evento de éxito (cached)
                await self._event_bus.publish(
                    ArticleQualityCalculated(
                        article_id=command.article_id,
                        success=True,
                        quality_score=quality_score,
                    )
                )

                return CalculateArticleQualityResult.success_result(
                    article_id=command.article_id,
                    quality_score=quality_score,
                    quality_level=str(article.quality.quality_level),
                )

            # 3. Verificar que tiene contenido para analizar
            if not article.content.markdown:
                self._logger.warning(
                    "Article sin content_markdown - no se puede calcular quality",
                    article_id=str(article_uuid),
                    title=(
                        str(article.metadata.title)[:100]
                        if article.metadata.title
                        else None
                    ),
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleQualityCalculated(
                        article_id=command.article_id,
                        success=False,
                        error_message="Artículo sin contenido markdown para analizar",
                    )
                )

                return CalculateArticleQualityResult.failure_result(
                    article_id=command.article_id,
                    message="Artículo sin contenido markdown para analizar",
                    error_code="NO_CONTENT_MARKDOWN",
                )

            # 4. Calcular quality score usando el domain service
            if self._quality_service is None:
                raise ValueError("Quality scorer service no disponible")

            quality_score = self._quality_service.calculate_content_quality_score(
                article
            )

            # 5. Convertir score a level usando Level VO
            quality_level = Level.from_score(quality_score)

            # 6. Actualizar artículo si se solicita (dentro de transacción)
            # NOTA: Solo establecemos quality_level, el score se deriva automáticamente
            if command.update_article:
                # Crear NUEVA sesión para esta invocación
                from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
                    RssArticleWriteRepository,
                )
                from src.shared.kernel.uow import SqlAlchemyUnitOfWork

                session = self._session_factory()
                repository = RssArticleWriteRepository(
                    session=session, logger=self._logger
                )
                uow = SqlAlchemyUnitOfWork(session=session, logger=self._logger)

                async with uow:
                    article.update_quality_assessment(quality_level=quality_level)
                    await repository.save(article)
                    await uow.commit()

                self._logger.debug(
                    "Quality calculado y guardado",
                    article_id=str(article_uuid),
                    quality_score=quality_score,
                    quality_level=str(quality_level),
                )

            # Emitir evento de éxito
            await self._event_bus.publish(
                ArticleQualityCalculated(
                    article_id=command.article_id,
                    success=True,
                    quality_score=quality_score,
                )
            )

            return CalculateArticleQualityResult.success_result(
                article_id=command.article_id,
                quality_score=quality_score,
                quality_level=str(quality_level),
            )

        except Exception as e:
            self._logger.exception(
                "❌ Error en CalculateArticleQualityHandler",
                article_id=command.article_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleQualityCalculated(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            return CalculateArticleQualityResult.failure_result(
                article_id=command.article_id,
                message=str(e),
                error_code="INTERNAL_ERROR",
            )
