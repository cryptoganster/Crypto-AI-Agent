"""Get scheduler status endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from src.shared.kernel.scheduler import IAPScheduler

from .dependencies import get_scheduler


async def get_scheduler_status(
    scheduler: IAPScheduler = Depends(get_scheduler),
) -> Dict[str, Any]:
    """
    GET /api/v1/scheduler/status

    Obtiene estado del scheduler y jobs activos.

    Returns:
        Dict con:
        - scheduler: Estado del scheduler
        - jobs: Lista de jobs registrados con su estado
    """
    try:
        return {
            "scheduler": scheduler.get_scheduler_status(),
            "jobs": scheduler.list_jobs(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado del scheduler: {str(e)}",
        )
