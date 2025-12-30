"""Handler para ExtractArticleKeywords command."""

import time
from typing import Dict, List, Optional
from uuid import UUID

from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.interfaces.services.keyword import (
    IArticleKeywordService,
)
from src.rss.article.domain.value_objects import ArticleId

# Value Objects
from src.rss.article.domain.value_objects.analysis import (
    KeywordExtractionConfig,
    KeywordScore,
)
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import ExtractArticleKeywordsCommand
from .interface import IExtractArticleKeywordsHandler
from .result import KeywordExtractionResult
from .validator import ExtractArticleKeywordsValidator


class ExtractArticleKeywordsHandler(IExtractArticleKeywordsHandler):
    """
    Handler para extraer keywords de un artículo usando IArticleKeywordService.

    RESPONSABILIDAD ÚNICA: Extracción de keywords
    - NO hace análisis de sentimiento
    - NO hace categorización
    - NO hace validación de calidad

    DELEGACIÓN: Usa IArticleKeywordService.extract_keywords_with_scores()

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
        keyword_service: Optional[IArticleKeywordService],
        validator: ExtractArticleKeywordsValidator,
        logger: ILogger,
    ):
        self._session_factory = session_factory
        self._keyword_service = keyword_service
        self._validator = validator
        self._logger = logger.bind(
            layer="application", component="ExtractArticleKeywordsHandler"
        )

    async def handle(
        self, command: ExtractArticleKeywordsCommand
    ) -> KeywordExtractionResult:
        """
        Extrae keywords de un artículo.

        Flujo:
        1. Validar comando
        2. Recuperar artículo
        3. Extraer keywords con IArticleAnalysisService
        4. Persistir keywords en Article (si save_to_article=True)
        5. Retornar resultado
        """
        start_time = time.time()

        self._logger.debug(
            "Iniciando extracción de keywords",
            article_id=command.article_id,
            max_keywords=command.max_keywords,
            correlation_id=command.correlation_id,
        )

        # 1. Validar comando
        validation_result = self._validator.validate(command)
        if not validation_result.is_valid:
            self._logger.error(
                "Validación de comando fallida",
                article_id=command.article_id,
                validation_errors=validation_result.errors,
                command_params={
                    "max_keywords": command.max_keywords,
                    "min_keyword_score": command.min_keyword_score,
                    "language": command.language,
                    "triggered_by": command.triggered_by,
                },
            )
            return KeywordExtractionResult.failure_result(
                article_id=command.article_id,
                message=f"Validación fallida: {'; '.join(validation_result.errors)}",
                error_code="VALIDATION_ERROR",
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
                "Artículo no encontrado", article_id=command.article_id
            )
            return KeywordExtractionResult.article_not_found(command.article_id)

        # 3. Verificar contenido suficiente (mínimo 100 caracteres)
        content_markdown = article.content.markdown
        if not content_markdown or len(content_markdown.strip()) < 100:
            self._logger.warning(
                "Contenido insuficiente para extraer keywords",
                article_id=command.article_id,
                content_length=len(content_markdown) if content_markdown else 0,
            )
            return KeywordExtractionResult.insufficient_content(command.article_id)

        # 4. Crear configuración de extracción usando VO
        config = KeywordExtractionConfig(
            max_keywords=command.max_keywords,
            min_score=command.min_keyword_score,
        )

        self._logger.debug(
            "Configuración de extracción creada",
            max_keywords=config.max_keywords,
            min_score=config.min_score,
            is_strict=config.is_strict(),
            is_permissive=config.is_permissive(),
        )

        # 5. Usar idioma ya detectado y guardado en BD (por DetectArticleLanguageCommand)
        # NOTA: El pipeline ejecuta DetectArticleLanguage ANTES de ExtractKeywords
        article_language = (
            article.metadata.language.code if article.metadata.language else "es"
        )  # Fallback a español si no detectado

        self._logger.debug(
            "Usando idioma del artículo",
            article_id=command.article_id,
            language=article_language,
        )

        # 6. Extraer keywords usando domain service dedicado
        try:
            # Usar extract_keywords_with_scores para obtener keywords y scores reales
            if self._keyword_service is None:
                raise ValueError("Keyword extractor service no disponible")

            keyword_scores = self._keyword_service.extract_keywords_with_scores(
                article=article,
                max_keywords=config.max_keywords,
                min_score=config.min_score,
            )

            if not keyword_scores:
                self._logger.info(
                    "No se encontraron keywords",
                    article_id=command.article_id,
                )
                return KeywordExtractionResult.no_keywords_found(command.article_id)

            # Convertir a lista ordenada por score
            keywords = list(keyword_scores.keys())

            # Crear KeywordScore VOs para análisis adicional
            keyword_score_vos = [
                KeywordScore(
                    keyword=kw, score=score, frequency=1
                )  # frequency no disponible aquí
                for kw, score in keyword_scores.items()
            ]

            # Analizar relevancia
            highly_relevant = [
                ks for ks in keyword_score_vos if ks.is_highly_relevant()
            ]
            moderately_relevant = [
                ks for ks in keyword_score_vos if ks.is_moderately_relevant()
            ]

            self._logger.debug(
                "Keywords extraídas",
                article_id=command.article_id,
                keywords_count=len(keywords),
                highly_relevant_count=len(highly_relevant),
                moderately_relevant_count=len(moderately_relevant),
                keywords=keywords,
            )

        except Exception as e:
            self._logger.exception(
                f"Error extrayendo keywords: {str(e)}",
                article_id=command.article_id,
                error_type=type(e).__name__,
            )
            return KeywordExtractionResult.failure_result(
                article_id=command.article_id,
                message=f"Error extrayendo keywords: {str(e)}",
                error_code="EXTRACTION_ERROR",
            )

        # 7. Persistir keywords en Article (opcional)
        keywords_saved = 0
        if command.save_to_article:
            try:
                # Verificar si ya tiene keywords
                if (
                    article.metadata.keywords is not None
                    and article.metadata.keywords.keywords
                    and not command.override_existing
                ):
                    self._logger.debug(
                        "Keywords ya existen, skip persistencia",
                        article_id=command.article_id,
                    )
                else:
                    # Unit of Work: Transacción atómica
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
                        # Asignar keywords al agregado
                        article.set_keywords(keywords)
                        await repository.save(article)

                        # Commit explícito
                        await uow.commit()

                        keywords_saved = len(keywords)

                    self._logger.debug(
                        "Keywords guardadas en artículo",
                        article_id=command.article_id,
                        keywords_count=keywords_saved,
                    )
            except Exception as e:
                self._logger.error(
                    f"Error guardando keywords: {str(e)}",
                    article_id=command.article_id,
                )
                # No fallar el comando, solo loggear error

        # 8. Calcular tiempo de procesamiento
        processing_time_ms = (time.time() - start_time) * 1000

        self._logger.debug(
            "Extracción de keywords completada",
            article_id=command.article_id,
            keywords_count=len(keywords),
            processing_time_ms=processing_time_ms,
        )

        return KeywordExtractionResult.success_result(
            article_id=command.article_id,
            keywords=keywords,
            keyword_scores=keyword_scores,
            extraction_method="tfidf",
            language_detected=article_language,
            language_confidence=1.0,  # Ya viene de BD, asumimos confianza alta
            keywords_saved=keywords_saved,
            processing_time_ms=processing_time_ms,
            highly_relevant_count=len(highly_relevant),
            moderately_relevant_count=len(moderately_relevant),
        )
