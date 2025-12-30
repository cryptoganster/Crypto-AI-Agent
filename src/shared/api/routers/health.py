"""Health check router."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

health_router = APIRouter()


@health_router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint with database verification.

    Args:
        request: FastAPI request with app state

    Returns:
        JSON response with health status
    """
    try:
        container = request.app.state.container

        # Verificar que el container esté inicializado
        if not container:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Container not initialized",
                },
            )

        # Verificar conexión a base de datos con query real
        db_status = "healthy"
        try:
            async with container.infra.session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as db_error:
            logger.error(f"Database health check failed: {db_error}")
            db_status = "unhealthy"

        overall_status = "healthy" if db_status == "healthy" else "unhealthy"
        status_code = 200 if overall_status == "healthy" else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall_status,
                "version": "1.0.0",
                "components": {
                    "api": "healthy",
                    "database": db_status,
                    "bootstrap": "healthy",
                },
            },
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)},
        )


@health_router.get("/metrics")
async def metrics():
    """
    Metrics endpoint (Prometheus format).

    TODO: Implement proper Prometheus metrics

    Returns:
        JSON response with metrics
    """
    return JSONResponse(
        status_code=200,
        content={
            "metrics": {
                "requests_total": 0,
                "errors_total": 0,
                "active_fetch_sessions": 0,
                "articles_processed": 0,
            }
        },
    )
