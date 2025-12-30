"""Scheduler router - Gestión de jobs programados."""

from fastapi import APIRouter

from .get_metrics import get_scheduler_metrics
from .get_scheduler_status import get_scheduler_status
from .list_jobs import list_jobs
from .pause_job import pause_job
from .resume_job import resume_job
from .trigger_job import trigger_job

router = APIRouter()

# Register all scheduler endpoints
router.add_api_route("/status", get_scheduler_status, methods=["GET"])
router.add_api_route("/jobs", list_jobs, methods=["GET"])
router.add_api_route("/jobs/{job_id}/pause", pause_job, methods=["POST"])
router.add_api_route("/jobs/{job_id}/resume", resume_job, methods=["POST"])
router.add_api_route("/jobs/{job_id}/trigger", trigger_job, methods=["POST"])
router.add_api_route("/metrics", get_scheduler_metrics, methods=["GET"])

__all__ = ["router"]
