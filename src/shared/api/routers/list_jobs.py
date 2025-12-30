"""List scheduler jobs endpoint."""

from typing import Any, Dict, List

from fastapi import Depends, HTTPException, status

from src.shared.kernel.scheduler import IAPScheduler

from .dependencies import get_scheduler


async def list_jobs(
    scheduler: IAPScheduler = Depends(get_scheduler),
) -> List[Dict[str, Any]]:
    """
    GET /api/v1/scheduler/jobs

    Lista todos los jobs registrados en el scheduler.

    Returns:
        Lista de jobs con su información:
        - id: ID único del job
        - name: Nombre descriptivo
        - next_run_time: Próxima ejecución
        - trigger: Tipo de trigger (interval/cron)
        - is_paused: Si está pausado
        - metadata: Información adicional
    """
    try:
        return scheduler.list_jobs()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando jobs: {str(e)}",
        )
