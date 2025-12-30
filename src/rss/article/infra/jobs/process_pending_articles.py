"""Job periódico para procesar artículos pendientes.

Este job se ejecuta periódicamente para asegurar que todos los artículos
tengan su contenido scrapeado, incluso si el evento ScrapingCompleted falló
o si quedaron artículos sin procesar.

Responsabilidades:
- Consultar artículos pendientes (sin content_scraped)
- Emitir ScrapeArticleContentCommand para cada uno
- Procesar en batches para evitar sobrecarga
- Logging detallado para observabilidad

Configuración:
- Intervalo: Cada 5 minutos (configurable)
- Batch size: 20 artículos por ejecución
- Max batches: 5 (máximo 100 artículos por ejecución)
"""

import asyncio
from typing import Optional

from src.shared.kernel import IMediator
from src.shared.kernel.logger import ILogger


async def process_pending_articles_job(
    mediator: IMediator,
    logger: ILogger,
    batch_size: int = 20,
    max_batches: int = 5,
) -> dict:
    """
    Job para procesar artículos pendientes de scraping.

    Este job:
    1. Consulta artículos sin content_scraped
    2. Emite ScrapeArticleContentCommand para cada uno
    3. Procesa en batches para evitar sobrecarga
    4. Retorna estadísticas de ejecución

    Args:
        mediator: Mediator para enviar queries y commands
        logger: Logger para observabilidad
        batch_size: Tamaño de cada batch (default: 20)
        max_batches: Máximo número de batches (default: 5)

    Returns:
        Dict con estadísticas de ejecución:
        - success: bool
        - total_processed: int
        - batches_processed: int
        - errors: int
        - duration_seconds: float
    """
    job_logger = logger.bind(
        layer="infrastructure",
        component="ProcessPendingArticlesJob",
    )

    job_logger.info(
        "🔄 Iniciando job de procesamiento de artículos pendientes",
        batch_size=batch_size,
        max_batches=max_batches,
    )

    import time

    start_time = time.time()

    total_processed = 0
    batch_number = 0
    errors = 0

    try:
        from src.rss.article.app.commands.scrape_content import (
            ScrapeArticleContentCommand,
        )
        from src.rss.article.app.queries.get_pending.query import (
            GetPendingArticlesQuery,
        )

        while batch_number < max_batches:
            batch_number += 1

            # Consultar siguiente batch
            query = GetPendingArticlesQuery(limit=batch_size)
            result = await mediator.send(query)

            if not result.success:
                job_logger.error(
                    "Error obteniendo artículos pendientes",
                    batch_number=batch_number,
                    error=result.error_message,
                )
                errors += 1
                break

            if not result.articles:
                job_logger.info(
                    "No hay más artículos pendientes",
                    total_processed=total_processed,
                    batches_processed=batch_number - 1,
                )
                break

            batch_count = len(result.articles)
            job_logger.info(
                f"📦 Procesando batch {batch_number}/{max_batches}",
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

                    job_logger.debug(
                        "Emitiendo ScrapeArticleContentCommand",
                        article_id=str(article_dto.id),
                        batch_number=batch_number,
                    )

                    # Emitir comando
                    await mediator.send(command)
                    total_processed += 1

                except Exception as e:
                    job_logger.error(
                        "Error emitiendo ScrapeArticleContentCommand",
                        article_id=str(article_dto.id),
                        batch_number=batch_number,
                        error=str(e),
                    )
                    errors += 1
                    # Continuar con los demás artículos
                    continue

            # Si el batch fue menor que el límite, no hay más artículos
            if batch_count < batch_size:
                job_logger.info(
                    "Último batch procesado (batch incompleto)",
                    total_processed=total_processed,
                    batches_processed=batch_number,
                )
                break

            # Pequeña pausa entre batches para no sobrecargar
            await asyncio.sleep(1)

        duration = time.time() - start_time

        # Log final
        if batch_number >= max_batches:
            job_logger.warning(
                "⚠️ Límite de batches alcanzado - pueden quedar artículos pendientes",
                total_processed=total_processed,
                max_batches=max_batches,
                duration_seconds=duration,
            )
        else:
            job_logger.success(
                "✅ Job completado exitosamente",
                total_processed=total_processed,
                batches_processed=batch_number,
                errors=errors,
                duration_seconds=duration,
            )

        return {
            "success": True,
            "total_processed": total_processed,
            "batches_processed": batch_number,
            "errors": errors,
            "duration_seconds": duration,
        }

    except Exception as e:
        duration = time.time() - start_time

        job_logger.exception(
            "❌ Error ejecutando job de procesamiento",
            total_processed=total_processed,
            batch_number=batch_number,
            errors=errors,
            duration_seconds=duration,
            error=str(e),
        )

        return {
            "success": False,
            "total_processed": total_processed,
            "batches_processed": batch_number,
            "errors": errors + 1,
            "duration_seconds": duration,
            "error": str(e),
        }


async def process_pending_articles_job_wrapper(
    mediator: IMediator,
    logger: ILogger,
    batch_size: Optional[int] = None,
    max_batches: Optional[int] = None,
) -> None:
    """
    Wrapper para el job que maneja excepciones y logging.

    Este wrapper asegura que el job nunca falle silenciosamente.

    Args:
        mediator: Mediator para enviar queries y commands
        logger: Logger para observabilidad
        batch_size: Tamaño de cada batch (opcional)
        max_batches: Máximo número de batches (opcional)
    """
    try:
        result = await process_pending_articles_job(
            mediator=mediator,
            logger=logger,
            batch_size=batch_size or 20,
            max_batches=max_batches or 5,
        )

        if not result["success"]:
            logger.error(
                "Job de procesamiento falló",
                result=result,
            )

    except Exception as e:
        logger.exception(
            "Error crítico en job de procesamiento",
            error=str(e),
        )
