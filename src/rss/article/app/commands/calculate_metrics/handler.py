"""Handler para CalculateArticleMetrics command."""

from uuid import UUID

from src.rss.article.domain.events import ArticleMetricsCalculated
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services import (
    IArticleMetricsCalculationService,
)
from src.rss.article.domain.value_objects import ArticleId
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import CalculateArticleMetricsCommand
from .exception import ArticleNotFoundError
from .interface import ICalculateArticleMetricsHandler
from .result import CalculateArticleMetricsResult
from .validator import CalculateArticleMetricsValidator


class CalculateArticleMetricsHandler(ICalculateArticleMetricsHandler):
    """
    Handler para calcular métricas de artículo (word_count, reading_time).

    RESPONSABILIDAD ÚNICA: Coordinar cálculo de métricas.
    DELEGACIÓN: Usa IArticleMetricsCalculationService.calculate_metrics_from_text()

    CQRS ESTRICTO:
    - NO usa ReadRepository (datos vienen del evento anterior)
    - Solo usa WriteRepository para persistir cambios
    - Confía en que el command tiene todos los datos necesarios

    UNIT OF WORK:
    - Usa UoW para manejar transacciones
    - Commit explícito después de save
    - Eventos publicados FUERA de transacción
    """

    def __init__(
        self,
        session_factory,  # Callable[[], AsyncSession]
        metrics_service: IArticleMetricsCalculationService,
        validator: CalculateArticleMetricsValidator,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        self._session_factory = session_factory
        self._metrics_service = metrics_service
        self._validator = validator
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application",
            component="CalculateArticleMetricsHandler",
        )

    async def handle(
        self, command: CalculateArticleMetricsCommand
    ) -> CalculateArticleMetricsResult:
        """
        Calcula métricas de artículo.

        Flujo:
        1. Validar comando
        2. Recuperar artículo
        3. Calcular métricas con service
        4. Persistir si update_article=True
        5. Retornar resultado
        """
        self._logger.debug(
            "Iniciando cálculo de métricas",
            article_id=command.article_id,
            force_recalculate=command.force_recalculate,
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
                ArticleMetricsCalculated(
                    article_id=command.article_id,
                    success=False,
                    error_message=f"Validación fallida: {'; '.join(validation_result.errors)}",
                )
            )

            return CalculateArticleMetricsResult.failure_result(
                article_id=ArticleId(command.article_id),
                error_message=f"Validación fallida: {'; '.join(validation_result.errors)}",
            )

        # CQRS Estricto: Validar que el command tenga los datos requeridos
        if not command.plaintext:
            error_msg = "plaintext is required in command (debe venir del evento ArticleMarkdownConverted)"
            self._logger.error(
                error_msg,
                article_id=command.article_id,
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleMetricsCalculated(
                    article_id=command.article_id,
                    success=False,
                    error_message=error_msg,
                )
            )

            return CalculateArticleMetricsResult.failure_result(
                article_id=ArticleId(command.article_id),
                error_message=error_msg,
            )

        # Crear ArticleId para retornos
        article_id = ArticleId(command.article_id)

        # 2. Calcular métricas usando domain service (sin leer aggregate)
        try:
            word_count, reading_time_minutes = (
                self._metrics_service.calculate_metrics_from_text(command.plaintext)
            )

            self._logger.debug(
                "Métricas calculadas exitosamente",
                article_id=command.article_id,
                word_count=word_count,
                reading_time_minutes=reading_time_minutes,
            )
        except Exception as e:
            self._logger.exception(
                "❌ ERROR calculando métricas",
                article_id=command.article_id,
                error=str(e),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleMetricsCalculated(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            return CalculateArticleMetricsResult.failure_result(
                article_id=article_id,
                error_message=str(e),
            )

        # 3. Unit of Work: Transacción atómica
        if command.update_article:
            # Crear NUEVA sesión para esta invocación
            from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
                RssArticleWriteRepository,
            )
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            session = self._session_factory()
            repository = RssArticleWriteRepository(session=session, logger=self._logger)
            uow = SqlAlchemyUnitOfWork(session=session, logger=self._logger)

            async with uow:
                # Cargar aggregate desde write side (WriteRepository.load)
                article_id_uuid = UUID(command.article_id)
                article = await repository.load(article_id_uuid)

                if not article:
                    raise ArticleNotFoundError(command.article_id)

                # Actualizar métricas en aggregate
                article.update_metrics(
                    word_count=word_count,
                    reading_time=reading_time_minutes,
                )
                await repository.save(article)

                # Commit explícito
                await uow.commit()

        # 4. Emitir evento ENRIQUECIDO con datos para siguiente paso
        # IMPORTANTE: Eventos publicados FUERA de transacción
        await self._event_bus.publish(
            ArticleMetricsCalculated(
                article_id=command.article_id,
                success=True,
                word_count=word_count,
                reading_time_minutes=reading_time_minutes,
                plaintext=command.plaintext,  # Para siguiente handler
                article_url=command.article_url,
                article_title=command.article_title,
            )
        )

        return CalculateArticleMetricsResult.success_result(
            article_id=article_id,
            word_count=word_count,
            reading_time_minutes=reading_time_minutes,
            was_updated=command.update_article,
        )
