"""Resume job endpoint."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from src.shared.kernel.scheduler import IAPScheduler

from .dependencies import get_scheduler


async def resume_job(
    job_id: str, scheduler: IAPScheduler = Depends(get_scheduler)
) -> Dict[str, Any]:
    """
    POST /api/v1/scheduler/jobs/{job_id}/resume

    Reanuda un job pausado.

    Args:
        job_id: ID del job a reanudar

    Returns:
        Dict con resultado de la operación
    """
    try:
        success = scheduler.start_task(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' no encontrado",
            )

        return {
            "job_id": job_id,
            "status": "resumed",
            "message": f"Job '{job_id}' reanudado exitosamente",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reanudando job '{job_id}': {str(e)}",
        )
