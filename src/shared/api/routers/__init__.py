"""Shared API routers - System, Scheduler, Health, Info, Root."""

from .health import health_router
from .info import info_router
from .root import root_router
from .scheduler import router as scheduler_router
from .system import router as system_router

__all__ = [
    "system_router",
    "scheduler_router",
    "health_router",
    "info_router",
    "root_router",
]
