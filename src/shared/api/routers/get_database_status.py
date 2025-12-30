"""Get database status endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from .dependencies import get_system_container


async def get_database_status(system=Depends(get_system_container)) -> Dict[str, Any]:
    """
    **Query:** GetSystemHealthAdapter (CQRS Read Side)

    Obtiene estado detallado de la base de datos.
    """
    try:
        health_adapter = system.infra.query_adapters.get_system_health_adapter()
        db_status = await health_adapter.get_database_status()

        return {"status": db_status.get("status", "unknown"), "details": db_status}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
