"""FastAPI application factory."""

from fastapi import FastAPI

from src.bootstrap.lifespan import lifespan
from src.bootstrap.middleware import setup_middleware
from src.bootstrap.routers import setup_routers


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Scraping Service",
        description="Microservicio de agregación de contenido RSS",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    setup_middleware(app)
    setup_routers(app)

    return app
