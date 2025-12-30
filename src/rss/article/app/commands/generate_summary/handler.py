"""Handler para GenerateArticleSummary command."""

import time
from typing import Optional
from uuid import UUID

from src.rss.article.domain.events import ArticleSummaryGenerated
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services import IArticleSummaryExtractionService
from src.rss.article.domain.value_objects import ArticleId
from src.rss.article.domain.value_objects.metadata import ArticleSummary
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import GenerateArticleSummaryCommand
from .exception import ArticleHasNoContentError, ArticleNotFoundError
from .interface import IGenerateArticleSummaryHandler
from .result import GenerateArticleSummaryResult
from .validator import GenerateArticleSummaryValidator


class GenerateArticleSummaryHandler(IGenerateArticleSummaryHandler):
    """
    Handler para generar summary de artículo.

    RESPONSABILIDAD ÚNICA: Coordinar generación de summary.
    DELEGACIÓN: Usa IArticleSummaryExtractionService.generate_summary()

    CQRS ESTRICTO:
    - Solo usa WriteRepository para persistir cambios
    - Datos vienen del evento anterior

    UNIT OF WORK:
    - Usa UoW para manejar transacciones
    - Commit explícito después de save
    - Eventos publicados FUERA de transacción
    """

    def __init__(
        self,
        session_factory,  # Callable[[], AsyncSession]
        summary_service: IArticleSummaryExtractionService,
        validator: GenerateArticleSummaryValidator,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        self._session_factory = session_factory
        self._summary_service = summary_service
        self._validator = validator
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application",
            component="GenerateArticleSummaryHandler",
        )

    async def handle(
        self, command: GenerateArticleSummaryCommand
    ) -> GenerateArticleSummaryResult:
        """
        Genera summary de artículo.

        Flujo:
        1. Validar comando
        2. Recuperar artículo
        3. Generar summary con service
        4. Persistir si update_article=True
        5. Retornar resultado
        """
        self._logger.debug(
            "Iniciando generación de summary",
            article_id=command.article_id,
            summary_length=command.summary_length,
        )

        # 1. Validar comando
        validation_result = self._validator.validate(command)
        if not validation_result.is_valid:
            self._logger.error(
                "Validación de comando fallida",
                article_id=command.article_id,
                validation_errors=validation_result.errors,
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleSummaryGenerated(
                    article_id=command.article_id,
                    success=False,
                    error_message=f"Validación fallida: {'; '.join(validation_result.errors)}",
                )
            )

            return GenerateArticleSummaryResult.failure_result(
                article_id=ArticleId(command.article_id),
                error_message=f"Validación fallida: {'; '.join(validation_result.errors)}",
            )

        # 2. Cargar artículo usando WriteRepository (CQRS estricto)
        # Crear sesión temporal para lectura inicial
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )

        read_session = self._session_factory()
        read_repository = RssArticleWriteRepository(
            session=read_session, logger=self._logger
        )

        article_id_uuid = UUID(command.article_id)
        article = await read_repository.load(article_id_uuid)

        # Crear ArticleId para retornos
        article_id = ArticleId(command.article_id)

        if not article:
            self._logger.warning(
                "Artículo no encontrado",
                article_id=command.article_id,
            )
            raise ArticleNotFoundError(command.article_id)

        # 3. Verificar contenido
        content_text = article.content.plaintext or article.content.markdown
        if not content_text:
            self._logger.warning(
                "Artículo sin contenido para generar resumen",
                article_id=command.article_id,
            )
            raise ArticleHasNoContentError(command.article_id)

        # 4. Verificar si ya generado
        if not command.force_regenerate:
            if article.summary:
                self._logger.debug(
                    "Summary ya generado",
                    article_id=command.article_id,
                    summary_length=len(article.summary),
                )

                # Emitir evento de éxito (cached)
                await self._event_bus.publish(
                    ArticleSummaryGenerated(
                        article_id=command.article_id,
                        success=True,
                        summary_length=len(article.summary),
                    )
                )

                return GenerateArticleSummaryResult.success_result(
                    article_id=article_id,
                    summary=article.summary,
                    was_updated=False,
                )

        # 5. Generar summary con domain service
        try:
            summary = self._summary_service.generate_summary(
                article,
                max_length=command.summary_length,
            )

            self._logger.debug(
                "Summary generado exitosamente",
                article_id=command.article_id,
                summary_length=len(summary),
            )

        except Exception as e:
            self._logger.exception(
                "❌ ERROR generando summary",
                article_id=command.article_id,
                error_type=type(e).__name__,
                error_message=str(e),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleSummaryGenerated(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            raise

        # 6. Persistir si se solicita (dentro de transacción)
        was_updated = False
        if command.update_article:
            try:
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
                    article.update_summary(summary=ArticleSummary(summary))
                    await repository.save(article)
                    await uow.commit()
                    was_updated = True

                self._logger.debug(
                    "Summary guardado",
                    article_id=command.article_id,
                    summary_length=len(summary),
                )
            except Exception as e:
                self._logger.exception(
                    "❌ ERROR guardando summary",
                    article_id=command.article_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleSummaryGenerated(
                        article_id=command.article_id,
                        success=False,
                        error_message=str(e),
                    )
                )

                raise

        # Emitir evento de éxito
        await self._event_bus.publish(
            ArticleSummaryGenerated(
                article_id=command.article_id,
                success=True,
                summary_length=len(summary),
            )
        )

        return GenerateArticleSummaryResult.success_result(
            article_id=article_id,
            summary=summary,
            was_updated=was_updated,
        )
