"""Job wrappers for APScheduler (pickle-serializable)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.main import AppContainer


async def scraping_job_task() -> None:
    """
    Tarea de scraping para APScheduler.

    Función a nivel de módulo para permitir serialización con pickle
    cuando se usa RedisJobStore.
    """
    from src.main import get_container
    from src.scraping.infra.jobs import start_scraping_job

    container = get_container()
    await start_scraping_job(container=container)


async def process_pending_articles_task() -> None:
    """
    Tarea de procesamiento de artículos pendientes para APScheduler.

    Función a nivel de módulo para permitir serialización con pickle
    cuando se usa RedisJobStore.

    Procesa artículos que quedaron sin content_scraped en batches.
    """
    from src.main import get_container
    from src.rss.article.infra.jobs import process_pending_articles_job_wrapper

    container = get_container()
    await process_pending_articles_job_wrapper(
        mediator=container.shared.mediator,
        logger=container.shared.logger,
        batch_size=20,  # 20 artículos por batch
        max_batches=5,  # Máximo 100 artículos por ejecución
    )
