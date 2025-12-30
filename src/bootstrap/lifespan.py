"""Application lifespan management."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from loguru import logger

from src.bootstrap.validation import (
    validate_critical_handlers,
    verify_event_driven_handlers,
)
from src.chunking.container import ChunkingContainer
from src.clustering.container import ClusteringContainer
from src.rss.article.container import ArticleContainer
from src.rss.feed.container import SourceContainer
from src.scraping.container import ScrapingContainer
from src.shared.config import AppConfig
from src.shared.container import SharedContainer
from src.shared.infra.scheduling.jobs import (
    process_pending_articles_task,
    scraping_job_task,
)


class AppContainer:
    """
    Container principal de la aplicación.

    Integra todos los bounded contexts:
    - Article: Gestión de artículos
    - Source: Gestión de fuentes RSS
    - Scraping: Scraping de contenido
    - Chunking: División de contenido en chunks + embeddings + vector store
    - Clustering: Agrupación semántica de artículos

    NOTA: EmbeddingContainer fue consolidado en ChunkingContainer.

    Requirements: 10.6.1
    """

    def __init__(self, config: AppConfig):
        """
        Inicializa el container de la aplicación.

        Args:
            config: Configuración de la aplicación
        """
        # 1. Shared Infrastructure
        self.shared = SharedContainer(config)

        # 2. Core Bounded Context Containers
        self.articles = ArticleContainer(self.shared)
        self.sources = SourceContainer(self.shared)
        self.scraping = ScrapingContainer(self.shared, self.articles, self.sources)

        # 3. AI/ML Bounded Context Containers
        self.chunking = ChunkingContainer(
            self.shared, self.articles
        )  # Incluye embedding + vector store
        self.clustering = ClusteringContainer(self.shared)

        # Config
        self.config = config

        # Alias para backward compatibility
        self.infra = self.shared
        self.fetching = self.scraping

    async def dispose(self):
        """Cleanup resources."""
        await self.infra.dispose()


# Global container instance
_container: Optional[AppContainer] = None


def get_container() -> AppContainer:
    """Get the global application container."""
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container


async def _startup(app: FastAPI) -> None:
    """
    Application startup logic.

    Args:
        app: FastAPI application instance
    """
    global _container

    logger.info("🚀 Starting Scraping Service...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")

    # Initialize container
    config = AppConfig()
    _container = AppContainer(config)
    app.state.container = _container

    system_logger = _container.infra.logger.bind(component="FastAPI")
    system_logger.info("✅ Application container initialized successfully")

    # Registrar handlers en el Mediator
    system_logger.info("Registrando handlers en Mediator...")

    # Core bounded contexts
    _container.articles.register_handlers()
    _container.sources.register_handlers()
    _container.scraping.register_handlers()

    # AI/ML bounded contexts (event-driven)
    _container.chunking.register_handlers()
    _container.clustering.register_handlers()

    system_logger.info("✅ Handlers registrados exitosamente")

    # Validar handlers críticos
    system_logger.info("Validando handlers críticos...")
    validate_critical_handlers(_container.shared.mediator, config)
    system_logger.info("✅ Handlers críticos validados")

    # Loggear resumen completo de handlers registrados
    system_logger.info("Generando resumen de handlers registrados...")
    _container.shared.log_registered_handlers_summary()

    # Verificar mediator
    mediator = _container.shared.mediator
    registered_handlers = mediator._handler_registry

    if registered_handlers:
        system_logger.info(
            "✅ Mediator inicializado con handlers registrados",
            handlers_count=len(registered_handlers),
            handlers=[cmd.__name__ for cmd in registered_handlers.keys()],
        )
    else:
        system_logger.warning("⚠️ Mediator inicializado pero sin handlers registrados")

    # Verificar handlers event-driven
    verify_event_driven_handlers(mediator, system_logger)

    system_logger.info(
        "API documentation available",
        docs_url="http://localhost:8000/api/docs",
        redoc_url="http://localhost:8000/api/redoc",
    )

    # Setup scheduler
    await _setup_scheduler(app, _container, system_logger)


async def _setup_scheduler(
    app: FastAPI, container: AppContainer, system_logger
) -> None:
    """
    Setup and start scheduler with jobs.

    Args:
        app: FastAPI application instance
        container: Application container
        system_logger: Logger instance
    """
    from src.shared.infra.scheduling.apscheduler import APScheduler

    config = container.config

    scheduler = APScheduler(
        logger=container.shared.logger,
        database_url=config.scheduler_database_url,
        redis_url=getattr(config, "redis_url", None),
        use_redis=getattr(config, "scheduler_use_redis", False),
        timezone="UTC",
    )

    # Start scheduler
    system_logger.info("Iniciando scheduler...")
    await scheduler.start()
    system_logger.info("✅ Scheduler started")

    # Register scraping job (every 5 minutes)
    scheduler.register_task(
        name="scraping",
        coroutine=scraping_job_task,
        interval_seconds=300,
        description="RSS Scraping (event-driven) every 5 min",
    )

    scheduler.start_task("scraping")
    system_logger.info(
        "✅ Scraping job registered and started (event-driven)",
        job_name="scraping",
        interval_minutes=5,
    )

    # Register process pending articles job (every 5 minutes)
    scheduler.register_task(
        name="process_pending_articles",
        coroutine=process_pending_articles_task,
        interval_seconds=300,
        description="Process pending articles (content scraping) every 5 min",
        run_on_startup=False,
    )

    scheduler.start_task("process_pending_articles")
    system_logger.info(
        "✅ Process pending articles job registered and started",
        job_name="process_pending_articles",
        interval_minutes=5,
    )

    # Trigger initial scraping in background
    async def trigger_initial_scraping():
        """Ejecuta el primer scraping en background con timeout."""
        await asyncio.sleep(2)
        system_logger.info("🎯 Ejecutando scraping inicial en background...")
        try:
            await asyncio.wait_for(scraping_job_task(), timeout=600.0)
        except asyncio.TimeoutError:
            system_logger.error("⏱️ Scraping inicial excedió timeout de 600s")
        except Exception as e:
            system_logger.exception("❌ Error en scraping inicial", error=str(e))

    asyncio.create_task(trigger_initial_scraping())
    system_logger.info(
        "✅ Scraping inicial programado en background (2s, timeout 600s)"
    )

    # Save scheduler in app state
    app.state.scheduler = scheduler

    system_logger.info(
        "✅ System started successfully",
        scraping_job="scraping",
        interval_minutes=5,
    )


async def _shutdown(app: FastAPI) -> None:
    """
    Application shutdown logic.

    Args:
        app: FastAPI application instance
    """
    logger.info("🛑 Shutting down Scraping Service...")

    if hasattr(app.state, "container"):
        system_logger = app.state.container.shared.logger.bind(component="FastAPI")

        # Stop scheduler gracefully
        if hasattr(app.state, "scheduler"):
            await app.state.scheduler.stop(wait=True)
            system_logger.info("✅ Scheduler stopped successfully")

        # Shutdown container
        await app.state.container.dispose()
        system_logger.info("✅ Container shutdown complete")

    logger.info("✅ Scraping Service shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        Control to application runtime
    """
    # Startup
    try:
        await _startup(app)
    except Exception as e:
        logger.error(f"❌ Error starting application: {e}")
        raise

    yield

    # Shutdown
    try:
        await _shutdown(app)
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
