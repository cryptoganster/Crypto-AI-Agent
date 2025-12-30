"""Root endpoint router."""

from fastapi import APIRouter

root_router = APIRouter()


@root_router.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Scraping Service API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/health",
    }
