"""Job para ejecutar el pipeline de scraping de sources RSS.

Este job inicia el scraping de todas las sources activas usando
arquitectura event-driven.

UBICACIÓN: src/scraping/infra/jobs/start_scraping.py
- Job pertenece al bounded context Scraping
- Usa StartScrapingCommand del mismo bounded context
- Inyección de dependencias explícita (no estado global)

ARQUITECTURA EVENT-DRIVEN:
1. Job → StartScrapingCommand (todas las sources activas)
2. Handler resuelve sources y emite ScrapingStarted
3. ScrapingPipeline coordina scraping de cada source
4. ScrapingPipeline emite ScrapingCompleted
5. ArticleContainer escucha y procesa artículos automáticamente

FLUJO COMPLETO (Event-Driven):
  Scheduler → start_scraping_job()
    ↓
  StartScrapingCommand
    ↓
  ScrapingPipeline (scraping de sources)
    ↓
  ScrapingCompleted event
    ↓
  OnScrapingCompletedHandler (ArticleContainer)
    ↓
  ContentExtractorPipeline (automático)
    ↓
  ContentAnalysisPipeline (automático)
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict

from src.scraping.app.commands.start_scraping import StartScrapingCommand

if TYPE_CHECKING:
    from src.main import AppContainer


async def start_scraping_job(
    container: "AppContainer",
    limit: int = 100,
    force_rescrape: bool = False,
) -> Dict[str, Any]:
    """
    Job que ejecuta el pipeline de scraping de sources RSS.

    Responsabilidad ÚNICA: Invocar StartScrapingCommand vía Mediator.
    El flujo event-driven se encarga del resto automáticamente.

    Args:
        container: Application container (inyectado por scheduler)
        limit: Límite de artículos por source (max_items_per_source)
        force_rescrape: Si True, fuerza refresh ignorando caché

    Returns:
        Dict con resultado de la ejecución

    Example:
        >>> # En scheduler
        >>> scheduler.register_task(
        ...     name="scraping",
        ...     coroutine=lambda: start_scraping_job(container=app_container),
        ...     interval_seconds=300,
        ... )
    """
    start_time = datetime.now(timezone.utc)

    try:
        logger = container.shared.logger.bind(component="ScrapingJob")
        mediator = container.shared.mediator

        logger.info(
            "Iniciando scraping job (event-driven)",
            limit=limit,
            force_rescrape=force_rescrape,
        )

        # Scrapear todas las sources activas
        command = StartScrapingCommand(
            source_ids=None,  # None = todas las activas
            max_items_per_source=limit,
            force_refresh=force_rescrape,
            correlation_id=f"scraping_job_{start_time.timestamp()}",
            triggered_by="scheduler",
        )

        result = await mediator.send(command)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        if result.success:
            logger.success(
                "Scraping job iniciado exitosamente",
                duration_seconds=duration,
                scraping_id=result.scraping_id,
                sources_count=result.sources_count,
            )
        else:
            logger.error(
                "Error iniciando scraping job",
                duration_seconds=duration,
                error=result.error if hasattr(result, "error") else "Unknown error",
            )

        return {
            "success": result.success,
            "duration_seconds": duration,
            "execution_time": start_time.isoformat(),
            "scraping_id": result.scraping_id,
            "sources_count": result.sources_count,
            "source_ids": list(result.source_ids) if result.source_ids else [],
            "error": result.error if hasattr(result, "error") else None,
        }

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        try:
            logger = container.shared.logger.bind(component="ScrapingJob")
            logger.exception("Scraping job falló", error=str(e))
        except:
            print(f"ERROR in scraping job: {e}")

        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
            "execution_time": start_time.isoformat(),
        }
