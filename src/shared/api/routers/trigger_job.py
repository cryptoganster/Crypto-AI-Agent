"""Trigger job manually endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from src.shared.kernel.scheduler import IAPScheduler

from .dependencies import get_scheduler


async def trigger_job(
    job_id: str, scheduler: IAPScheduler = Depends(get_scheduler)
) -> Dict[str, Any]:
    """
    POST /api/v1/scheduler/jobs/{job_id}/trigger

    Ejecuta un job manualmente (fuera de su schedule normal).

    Args:
        job_id: ID del job a ejecutar

    Returns:
        Dict con resultado:
        - job_id: ID del job
        - status: Estado de la operación
        - message: Mensaje descriptivo
    """
    try:
        success = scheduler.trigger_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' no encontrado",
            )

        return {
            "job_id": job_id,
            "status": "triggered",
            "message": f"Job '{job_id}' ejecutado manualmente",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando job '{job_id}': {str(e)}",
        )
