"""Handler para extracción de texto plano desde HTML."""

import time
from uuid import UUID

from src.rss.article.domain.events import ArticlePlaintextExtracted
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services import (
    IArticlePlaintextExtractionService,
)
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import ExtractArticlePlaintextCommand
from .exception import (
    ArticleNotFoundError,
    NoScrapedContentError,
    PlaintextConversionError,
)
from .result import PlaintextExtractionResult


class ExtractArticlePlaintextHandler:
    """
    Handler para extraer texto plano desde HTML scrapeado.

    PIPELINE: Fase 2 (después de Scraping, antes de Markdown)
    INPUT: content_scrapped (HTML) - del evento ArticleContentScraped
    OUTPUT: content_plaintext (texto puro)

    PROPÓSITO:
    - Preparar texto limpio para NLP (idioma, keywords, sentimiento)
    - Eliminar tags HTML, URLs, imágenes, scripts
    - Normalizar espacios para mejor procesamiento

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
        plaintext_service: IArticlePlaintextExtractionService,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        """
        Inicializa con dependencias inyectadas.

        CRÍTICO: Recibe session_factory en lugar de repository/uow pre-creados
        para crear una NUEVA sesión en cada invocación de handle().
        Esto evita problemas de concurrencia cuando múltiples eventos
        se procesan en paralelo.

        Args:
            session_factory: Factory para crear nuevas sesiones
            plaintext_service: Servicio de extracción de plaintext
            event_bus: Event bus para publicar eventos
            logger: Logger para registrar operaciones
        """
        self._session_factory = session_factory
        self._plaintext_service = plaintext_service
        self._event_bus = event_bus
        self._logger = logger

    async def handle(
        self, command: ExtractArticlePlaintextCommand
    ) -> PlaintextExtractionResult:
        """
        Ejecuta extracción de texto plano.

        Args:
            command: Comando con article_id y html_content del evento anterior

        Returns:
            PlaintextExtractionResult con resultado de extracción
        """
        start_time = time.time()

        self._logger.debug(
            "Iniciando extracción de plaintext",
            article_id=command.article_id,
            override_existing=command.override_existing,
            has_html_content=command.html_content is not None,
        )

        try:
            # CQRS Estricto: Validar que el command tenga los datos requeridos
            if not command.html_content:
                error_msg = "html_content is required in command (debe venir del evento ArticleContentScraped)"
                self._logger.error(
                    error_msg,
                    article_id=command.article_id,
                )
                raise NoScrapedContentError(command.article_id)

            # Extraer plaintext usando domain service (sin leer aggregate)
            try:
                plaintext = self._plaintext_service.extract_plaintext_from_html(
                    command.html_content
                )
            except Exception as e:
                raise PlaintextConversionError(command.article_id, e)

            # Crear NUEVA sesión para esta invocación
            from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
                RssArticleWriteRepository,
            )
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            session = self._session_factory()
            article_repository = RssArticleWriteRepository(
                session=session,
                logger=self._logger,
            )
            uow = SqlAlchemyUnitOfWork(
                session=session,
                logger=self._logger,
            )

            # Unit of Work: Transacción atómica
            async with uow:
                # Cargar aggregate desde write side (WriteRepository.load)
                article_id_uuid = UUID(command.article_id)
                article = await article_repository.load(article_id_uuid)

                if not article:
                    raise ArticleNotFoundError(command.article_id)

                # Aplicar cambios
                article.update_plaintext(plaintext=plaintext)

                # Guardar
                await article_repository.save(article)

                # Commit explícito
                await uow.commit()

            # 7. Calcular métricas
            word_count = len(plaintext.split())
            plaintext_length = len(plaintext)
            processing_time_ms = (time.time() - start_time) * 1000

            self._logger.info(
                "Plaintext extraído exitosamente",
                article_id=command.article_id,
                word_count=word_count,
                plaintext_length=plaintext_length,
                processing_time_ms=processing_time_ms,
            )

            # 8. Emitir evento ENRIQUECIDO con datos para siguiente paso
            # IMPORTANTE: Eventos publicados FUERA de transacción
            await self._event_bus.publish(
                ArticlePlaintextExtracted(
                    article_id=command.article_id,
                    success=True,
                    plaintext_length=plaintext_length,
                    plaintext=plaintext,  # ← NUEVO: Para siguiente handler
                    html_content=command.html_content,  # ← NUEVO: Para conversión markdown
                    article_url=command.article_url or str(article.metadata.url),
                    article_title=command.article_title or str(article.metadata.title),
                )
            )

            return PlaintextExtractionResult.success_result(
                article_id=command.article_id,
                plaintext_length=plaintext_length,
                word_count=word_count,
                processing_time_ms=processing_time_ms,
            )

        except (ArticleNotFoundError, NoScrapedContentError) as e:
            self._logger.warning(
                "Error validación de artículo",
                article_id=command.article_id,
                error=str(e),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticlePlaintextExtracted(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            return PlaintextExtractionResult.failure_result(
                article_id=command.article_id,
                message=str(e),
                error_code=type(e).__name__,
            )

        except PlaintextConversionError as e:
            self._logger.error(
                "Error convirtiendo HTML a plaintext",
                article_id=command.article_id,
                error=str(e.original_error),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticlePlaintextExtracted(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            return PlaintextExtractionResult.failure_result(
                article_id=command.article_id,
                message=str(e),
                error_code="CONVERSION_ERROR",
            )

        except Exception as e:
            self._logger.exception(
                "Error inesperado extrayendo plaintext",
                article_id=command.article_id,
                error=str(e),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticlePlaintextExtracted(
                    article_id=command.article_id,
                    success=False,
                    error_message=f"Unexpected error: {str(e)}",
                )
            )

            return PlaintextExtractionResult.failure_result(
                article_id=command.article_id,
                message=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )
