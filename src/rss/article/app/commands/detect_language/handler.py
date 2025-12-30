"""Handler para DetectArticleLanguage command."""

import time
from uuid import UUID

from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services import (
    IArticleLanguageDetectionService,
)
from src.rss.article.domain.value_objects import ArticleId
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import DetectArticleLanguageCommand
from .interface import IDetectArticleLanguageHandler
from .result import LanguageDetectionResult


class DetectArticleLanguageHandler(IDetectArticleLanguageHandler):
    """
    Handler para detectar idioma de artículos.

    RESPONSABILIDAD ÚNICA: Detección de idioma
    - NO extrae keywords
    - NO calcula métricas
    - NO genera resúmenes

    DELEGACIÓN: Usa IArticleLanguageDetectionService para lógica de dominio.

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
        language_detection_service: IArticleLanguageDetectionService,
        logger: ILogger,
    ):
        self._session_factory = session_factory
        self._language_detection_service = language_detection_service
        self._logger = logger.bind(
            layer="application", component="DetectArticleLanguageHandler"
        )

    async def handle(
        self, command: DetectArticleLanguageCommand
    ) -> LanguageDetectionResult:
        """
        Detecta idioma del artículo y persiste en BD.

        Flujo:
        1. Recuperar artículo
        2. Verificar contenido suficiente
        3. Detectar idioma con domain service
        4. Persistir usando article.update_language(language_code=, confidence=)
        5. Retornar resultado
        """
        start_time = time.time()

        self._logger.debug(
            "Iniciando detección de idioma",
            article_id=command.article_id,
            override_existing=command.override_existing,
            correlation_id=command.correlation_id,
        )

        # 1. Cargar artículo usando WriteRepository (CQRS estricto)
        # Crear sesión temporal para lectura inicial
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )

        read_session = self._session_factory()
        read_repository = RssArticleWriteRepository(
            session=read_session, logger=self._logger
        )

        article_id_str = (
            str(command.article_id)
            if not isinstance(command.article_id, str)
            else command.article_id
        )
        article_id_uuid = UUID(article_id_str)

        try:
            article = await read_repository.load(article_id_uuid)
        finally:
            # CRÍTICO: Cerrar sesión de lectura para devolver conexión al pool
            await read_session.close()

        # Crear ArticleId para retornos
        article_id = ArticleId(article_id_str)

        if not article:
            self._logger.warning(
                "Artículo no encontrado", article_id=command.article_id
            )
            return LanguageDetectionResult.article_not_found(command.article_id)

        # 2. Verificar si ya tiene idioma detectado
        # Ahora language=None por defecto, solo skip si tiene valor real
        if (
            article.metadata.language is not None
            and article.metadata.language.code is not None
            and not command.override_existing
        ):
            self._logger.debug(
                "Artículo ya tiene idioma detectado, skip detección",
                article_id=command.article_id,
                current_language=article.metadata.language.code,
            )
            return LanguageDetectionResult.success_result(
                article_id=command.article_id,
                language_detected=article.metadata.language.code,
                confidence=1.0,  # Asumimos alta confianza si ya existe
                language_saved=False,
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        # 3. Verificar contenido suficiente (content_plaintext preferido para NLP)
        # Mismo fallback que ArticleLanguageDetectionService
        text_to_analyze = (
            article.content.plaintext  # Mejor para NLP (sin HTML/Markdown)
            or article.content.markdown
            or article.content.markdown  # Fallback a markdown si no hay plaintext
        )
        if not text_to_analyze or len(text_to_analyze.strip()) < 50:
            self._logger.warning(
                "Contenido insuficiente para detectar idioma",
                article_id=command.article_id,
                content_length=len(text_to_analyze) if text_to_analyze else 0,
            )
            return LanguageDetectionResult.insufficient_content(command.article_id)

        # 4. Detectar idioma usando domain service
        try:
            detected_language = self._language_detection_service.detect_language(
                article
            )

            self._logger.debug(
                "Idioma detectado",
                article_id=command.article_id,
                language=detected_language.code,
                confidence=detected_language.confidence,
                is_high_confidence=detected_language.is_high_confidence(),
            )

            # 5. Persistir idioma en artículo (dentro de transacción)
            language_saved = False
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
                    article.update_language(
                        language_code=detected_language.code,
                        confidence=detected_language.confidence,
                    )
                    await repository.save(article)
                    await uow.commit()
                    language_saved = True

                self._logger.debug(
                    "Idioma guardado en artículo",
                    article_id=command.article_id,
                    language=detected_language.code,
                )
            except Exception as e:
                self._logger.error(
                    f"Error guardando idioma: {str(e)}",
                    article_id=command.article_id,
                )
                # No fallar el comando, solo loggear error

            # 6. Calcular tiempo de procesamiento
            processing_time_ms = (time.time() - start_time) * 1000

            self._logger.debug(
                "Detección de idioma completada",
                article_id=command.article_id,
                language=detected_language.code,
                confidence=detected_language.confidence,
                processing_time_ms=processing_time_ms,
            )

            return LanguageDetectionResult.success_result(
                article_id=command.article_id,
                language_detected=detected_language.code,
                confidence=detected_language.confidence,
                language_saved=language_saved,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            self._logger.exception(
                f"Error detectando idioma: {str(e)}",
                article_id=command.article_id,
                error_type=type(e).__name__,
            )
            return LanguageDetectionResult.failure_result(
                article_id=command.article_id,
                message=f"Error detectando idioma: {str(e)}",
                error_code="DETECTION_ERROR",
            )
