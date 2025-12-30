"""System router - Health checks y métricas del sistema."""

from fastapi import APIRouter

from .get_database_status import get_database_status
from .get_rss_service_status import get_rss_service_status
from .get_system_health import get_system_health
from .get_system_metrics import get_system_metrics

router = APIRouter()

# Register all system endpoints
router.add_api_route("/health", get_system_health, methods=["GET"])
router.add_api_route("/metrics", get_system_metrics, methods=["GET"])
router.add_api_route("/database/status", get_database_status, methods=["GET"])
router.add_api_route("/rss/status", get_rss_service_status, methods=["GET"])

__all__ = ["router"]
