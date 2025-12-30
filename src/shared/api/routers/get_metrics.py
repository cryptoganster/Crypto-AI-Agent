"""Get scheduler execution metrics endpoint."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import Depends, HTTPException, status

from src.shared.kernel.scheduler import IAPScheduler

from .dependencies import get_scheduler


async def get_scheduler_metrics(
    scheduler: IAPScheduler = Depends(get_scheduler),
) -> Dict[str, Any]:
    """
    GET /api/v1/scheduler/metrics

    Obtiene métricas detalladas de ejecución del scheduler.

    Returns:
        Dict con métricas agregadas:
        - scheduler_info: Estado general del scheduler
        - jobs_summary: Resumen de todos los jobs
        - execution_stats: Estadísticas de ejecución
    """
    try:
        # Estado general
        scheduler_status = scheduler.get_scheduler_status()

        # Información de jobs
        jobs = scheduler.list_jobs()

        # Calcular estadísticas
        total_jobs = len(jobs)
        running_jobs = sum(1 for job in jobs if not job.get("is_paused", True))
        paused_jobs = sum(1 for job in jobs if job.get("is_paused", False))

        # Jobs por tipo
        interval_jobs = sum(
            1 for job in jobs if "interval" in job.get("type", "").lower()
        )
        cron_jobs = sum(1 for job in jobs if "cron" in job.get("type", "").lower())

        return {
            "scheduler_info": {
                "running": scheduler_status.get("running", False),
                "healthy": scheduler_status.get("healthy", False),
                "state": scheduler_status.get("state", "unknown"),
                "timezone": scheduler_status.get("timezone", "UTC"),
                "uptime": _calculate_uptime(jobs),
            },
            "jobs_summary": {
                "total": total_jobs,
                "running": running_jobs,
                "paused": paused_jobs,
                "interval_based": interval_jobs,
                "cron_based": cron_jobs,
            },
            "jobs": jobs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo métricas del scheduler: {str(e)}",
        )


def _calculate_uptime(jobs: List[Dict[str, Any]]) -> float:
    """
    Calcula uptime aproximado basado en jobs activos.

    Args:
        jobs: Lista de jobs

    Returns:
        Uptime en segundos (aproximado)
    """
    # Simplemente retornar 0 por ahora
    # En el futuro podríamos trackear el start_time del scheduler
    return 0.0
