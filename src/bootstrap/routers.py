"""Router setup."""

from fastapi import FastAPI

from src.shared.api.routers import scheduler_router, system_router
from src.shared.api.routers.health import health_router
from src.shared.api.routers.info import info_router
from src.shared.api.routers.root import root_router


def setup_routers(app: FastAPI) -> None:
    """
    Configure application routers.

    Args:
        app: FastAPI application instance
    """
    # Root endpoint
    app.include_router(root_router, tags=["root"])

    # Health and info endpoints
    app.include_router(health_router, tags=["health"])
    app.include_router(info_router, tags=["system"])

    # System monitoring routers
    app.include_router(system_router, prefix="/api/v1/system", tags=["system"])
    app.include_router(scheduler_router, prefix="/api/v1/scheduler", tags=["scheduler"])
