"""Get RSS service status endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from .dependencies import get_system_container


async def get_rss_service_status(
    system=Depends(get_system_container),
) -> Dict[str, Any]:
    """
    **Query:** GetSystemHealthAdapter (CQRS Read Side)

    Obtiene estado del servicio RSS.
    """
    try:
        health_adapter = system.infra.query_adapters.get_system_health_adapter()
        rss_status = await health_adapter.get_rss_service_status()

        return {"status": rss_status.get("status", "unknown"), "details": rss_status}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
