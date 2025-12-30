"""Get system health endpoint."""

from fastapi import Depends, HTTPException, status

from src.shared.api.schemas import HealthResponse

from .dependencies import get_system_container


async def get_system_health(system=Depends(get_system_container)):
    """
    **Query:** GetSystemHealthAdapter (CQRS Read Side)

    Obtiene estado de salud del sistema completo.
    """
    try:
        health_adapter = system.infra.query_adapters.get_system_health_adapter()

        system_status = await health_adapter.get_system_status()
        db_status = await health_adapter.get_database_status()
        rss_status = await health_adapter.get_rss_service_status()
        uptime = await health_adapter.get_system_uptime()

        all_healthy = all(
            [
                system_status.get("status") == "healthy",
                db_status.get("status") == "healthy",
                rss_status.get("status") == "healthy",
            ]
        )

        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            version="1.0.0",
            uptime=uptime,
            components={
                "api": "healthy",
                "database": db_status.get("status", "unknown"),
                "rss_service": rss_status.get("status", "unknown"),
                "system": system_status.get("status", "unknown"),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}",
        )
