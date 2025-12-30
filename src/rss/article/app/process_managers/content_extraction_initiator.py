"""ContentExtractionInitiator - Process Manager para iniciar extracción de contenido.

Este Process Manager maneja eventos cross-bounded-context:

Cross-BC Event:
- ScrapingCompleted (del BC Scraping) → Inicia procesamiento de artículos

Responsabilidad:
- Escuchar ScrapingCompleted
- Consultar artículos pendientes usando Query Handler (CQRS)
- Emitir ScrapeArticleContentCommand para cada artículo pendiente

CQRS Estricto:
- Event Handler solo delega al Process Manager
- Process Manager usa Mediator para Queries y Commands
- NO accede directamente a ReadRepository
- Emite comandos para iniciar procesamiento
"""

from src.scraping.domain.events import ScrapingCompleted
from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


class ContentExtractionInitiator:
    """
    Process Manager para iniciar extracción de contenido después de scraping.

    Este es un Process Manager cross-bounded-context que conecta:
    - Scraping BC (ScrapingCompleted) → Article BC (ScrapeArticleContentCommand)

    Responsabilidades:
    - Escuchar ScrapingCompleted del BC Scraping
    - Consultar artículos pendientes usando Query Handler (CQRS)
    - Emitir ScrapeArticleContentCommand para cada artículo
    - Iniciar el pipeline de extracción de contenido

    CQRS Estricto:
    - Usa Mediator.send(GetPendingArticlesQuery) para obtener artículos
    - NO accede directamente a ReadRepository
    - Todo pasa por Mediator (Queries y Commands)
    """

    def __init__(
        self,
        mediator: IMediator,
        logger: ILogger,
    ):
        """
        Inicializa Process Manager.

        Args:
            mediator: Mediator para enviar Commands y Queries
            logger: Logger para observabilidad
        """
        self._mediator = mediator
        self._logger = logger.bind(
            layer="application",
            component="ContentExtractionInitiator",
        )

    async def on_scraping_completed(self, event: ScrapingCompleted) -> None:
        """
        Maneja ScrapingCompleted (cross-bounded-context).

        Consulta artículos pendientes en batches y emite comandos para procesarlos.

        Args:
            event: Evento de scraping completado
        """
        self._logger.info(
            "🔍 ScrapingCompleted recibido (cross-BC)",
            scraping_id=event.scraping_id,
            articles_new=event.articles_new,
            articles_discovered=event.articles_discovered,
            sources_successful=event.sources_successful,
        )

        # Procesar artículos pendientes en batches
        await self._process_pending_articles_in_batches(
            scraping_id=event.scraping_id,
            batch_size=10,
            max_batches=10,  # Máximo 100 artículos por evento
        )

    async def _process_pending_articles_in_batches(
        self,
        scraping_id: str,
        batch_size: int = 10,
        max_batches: int = 10,
    ) -> None:
        """
        Procesa artículos pendientes en batches.

        Consulta artículos pendientes en batches y emite comandos hasta que:
        - No haya más artículos pendientes
        - Se alcance el límite de batches

        Args:
            scraping_id: ID del scraping
            batch_size: Tamaño de cada batch
            max_batches: Máximo número de batches a procesar
        """
        from src.rss.article.app.commands.scrape_content import (
            ScrapeArticleContentCommand,
        )
        from src.rss.article.app.queries.get_pending.query import (
            GetPendingArticlesQuery,
        )

        total_processed = 0
        batch_number = 0

        try:
            while batch_number < max_batches:
                batch_number += 1

                # Consultar siguiente batch
                query = GetPendingArticlesQuery(limit=batch_size)
                result = await self._mediator.send(query)

                if not result.success:
                    self._logger.error(
                        "Error obteniendo artículos pendientes",
                        scraping_id=scraping_id,
                        batch_number=batch_number,
                        error=result.error_message,
                    )
                    break

                if not result.articles:
                    self._logger.info(
                        "No hay más artículos pendientes",
                        scraping_id=scraping_id,
                        total_processed=total_processed,
                        batches_processed=batch_number - 1,
                    )
                    break

                batch_count = len(result.articles)
                self._logger.info(
                    f"📦 Procesando batch {batch_number}/{max_batches}",
                    scraping_id=scraping_id,
                    batch_size=batch_count,
                    total_processed=total_processed,
                )

                # Emitir comando para cada artículo del batch
                for article_dto in result.articles:
                    try:
                        command = ScrapeArticleContentCommand(
                            article_id=str(article_dto.id),
                            force_rescrape=False,
                        )

                        self._logger.debug(
                            "Emitiendo ScrapeArticleContentCommand",
                            article_id=str(article_dto.id),
                            scraping_id=scraping_id,
                            batch_number=batch_number,
                        )

                        # Emitir comando (fire-and-forget)
                        await self._mediator.send(command)
                        total_processed += 1

                    except Exception as e:
                        self._logger.error(
                            "Error emitiendo ScrapeArticleContentCommand",
                            article_id=str(article_dto.id),
                            scraping_id=scraping_id,
                            batch_number=batch_number,
                            error=str(e),
                        )
                        # Continuar con los demás artículos
                        continue

                # Si el batch fue menor que el límite, no hay más artículos
                if batch_count < batch_size:
                    self._logger.info(
                        "Último batch procesado (batch incompleto)",
                        scraping_id=scraping_id,
                        total_processed=total_processed,
                        batches_processed=batch_number,
                    )
                    break

            # Log final
            if batch_number >= max_batches:
                self._logger.warning(
                    "⚠️ Límite de batches alcanzado - pueden quedar artículos pendientes",
                    scraping_id=scraping_id,
                    total_processed=total_processed,
                    max_batches=max_batches,
                )
            else:
                self._logger.success(
                    "✅ Todos los artículos pendientes procesados",
                    scraping_id=scraping_id,
                    total_processed=total_processed,
                    batches_processed=batch_number,
                )

        except Exception as e:
            self._logger.exception(
                "Error procesando artículos en batches",
                scraping_id=scraping_id,
                total_processed=total_processed,
                batch_number=batch_number,
                error=str(e),
            )
