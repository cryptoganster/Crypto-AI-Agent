"""Info endpoint router."""

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

info_router = APIRouter()


@info_router.get("/info")
async def info():
    """
    Service information endpoint.

    Returns:
        JSON response with service information
    """
    return JSONResponse(
        status_code=200,
        content={
            "service": "scraping-service",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "description": "Microservicio de agregación de contenido RSS",
        },
    )
