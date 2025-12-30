"""Handler para StartArticleProcessingCommand.

Este handler es el PUNTO DE ENTRADA ÚNICO para iniciar el procesamiento
completo de artículos (extracción + análisis) usando arquitectura event-driven.

Reemplaza a:
- RunArticleContentScrapingPipelineHandler (DEPRECATED)
- RunProcessingPipelineHandler (DEPRECATED)

Flujo event-driven:
1. StartArticleProcessingCommand → Handler obtiene artículos pendientes
2. Handler emite ContentExtractorPipelineStarted
3. ContentExtractorPipeline procesa (scraping, plaintext, markdown)
4. ContentExtractorPipeline emite ContentExtractorPipelineCompleted
5. ContentAnalysisPipeline procesa (metrics, language, summary, keywords, quality)
"""

import uuid
from datetime import datetime, timezone

from src.rss.article.app.commands.start_processing.command import (
    StartArticleProcessingCommand,
)
from src.rss.article.app.commands.start_processing.result import (
    StartArticleProcessingResult,
)
from src.rss.article.domain.events import ContentExtractorPipelineStarted
from src.rss.article.domain.interfaces.repositories import IArticleWriteRepository
from src.shared.kernel import IEventBus
from src.shared.kernel.logger import ILogger


class StartArticleProcessingHandler:
    """
    Handler para iniciar el pipeline completo de procesamiento de artículos.

    Responsabilidad única: Obtener artículos pendientes y emitir evento inicial.

    El flujo event-driven se encarga del resto:
    1. ContentExtractorPipelineStarted → ContentExtractorPipeline
       - Scraping de contenido HTML
       - Extracción de plaintext
       - Conversión a markdown
    2. ContentExtractorPipelineCompleted → ContentAnalysisPipeline
       - Cálculo de métricas
       - Detección de idioma
       - Generación de resumen
       - Extracción de keywords
       - Evaluación de calidad

    Este handler REEMPLAZA a:
    - RunArticleContentScrapingPipelineHandler (arquitectura síncrona antigua)
    - RunProcessingPipelineHandler (arquitectura síncrona antigua)

    CQRS ESTRICTO:
    - Usa WriteRepository (aunque solo lee, es un Command)

    UNIT OF WORK:
    - No persiste cambios (solo lee y emite eventos)
    - UoW disponible por consistencia del patrón
    """

    def __init__(
        self,
        article_repository: IArticleWriteRepository,
        session_factory,  # async_sessionmaker para crear sesiones nuevas
        event_bus: IEventBus,
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        ARQUITECTURA:
        - Recibe session_factory aunque no lo usa actualmente
        - Mantiene consistencia con patrón de otros handlers
        - Si en el futuro necesita UoW, puede crearlo bajo demanda

        Args:
            article_repository: Repository para obtener artículos (CQRS Write Side)
            session_factory: Factory para crear sesiones (patrón consistente)
            event_bus: Event bus para publicar eventos
            logger: Logger para registrar operaciones
        """
        self._article_repository = article_repository
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._logger = logger

    async def handle(
        self,
        command: StartArticleProcessingCommand,
    ) -> StartArticleProcessingResult:
        """
        Ejecuta el comando de iniciar procesamiento completo.

        Flujo:
        1. Obtiene artículos pendientes (sin contenido scrapeado)
        2. Genera pipeline ID único
        3. Emite ContentExtractorPipelineStarted
        4. Process managers event-driven se encargan del resto

        Args:
            command: Comando con configuración (limit, correlation_id)

        Returns:
            StartArticleProcessingResult con pipeline_id y article_ids

        Example:
            >>> command = StartArticleProcessingCommand(limit=100)
            >>> result = await handler.handle(command)
            >>> print(f"Pipeline {result.pipeline_id} iniciado con {len(result.article_ids)} artículos")
        """
        try:
            # 1. Obtener artículos pendientes de procesamiento
            # Prioridad: artículos sin contenido scrapeado
            articles = await self._article_repository.find_without_scraped_content(
                limit=command.limit
            )

            if not articles:
                self._logger.info("No hay artículos pendientes de procesamiento")
                return StartArticleProcessingResult.success_result(
                    pipeline_id="",
                    article_ids=[],
                )

            article_ids = [str(article.id) for article in articles]

            # 2. Generar pipeline ID único
            pipeline_id = command.correlation_id or f"pipeline_{uuid.uuid4()}"

            # 3. Emitir evento inicial para arquitectura event-driven
            event = ContentExtractorPipelineStarted(
                pipeline_id=pipeline_id,
                article_ids=article_ids,
                occurred_at=datetime.now(timezone.utc),
            )

            await self._event_bus.publish(event)

            self._logger.info(
                "Pipeline de procesamiento iniciado (event-driven)",
                pipeline_id=pipeline_id,
                article_count=len(article_ids),
                phases="extracción → análisis",
            )

            return StartArticleProcessingResult.success_result(
                pipeline_id=pipeline_id,
                article_ids=article_ids,
            )

        except Exception as e:
            self._logger.error(
                "Error iniciando pipeline de procesamiento",
                error=str(e),
            )
            return StartArticleProcessingResult.failure(str(e))
