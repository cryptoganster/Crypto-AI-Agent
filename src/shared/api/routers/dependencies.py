"""Dependencies for shared endpoints."""

from fastapi import Request

from src.shared.kernel.scheduler import IAPScheduler


def get_scheduler(request: Request) -> IAPScheduler:
    """
    Get scheduler via Dependency Injection from bootstrap container.

    Args:
        request: FastAPI request

    Returns:
        IAPScheduler instance
    """
    # Get scheduler from app state (set during lifespan)
    if hasattr(request.app.state, "scheduler"):
        return request.app.state.scheduler
    raise RuntimeError("Scheduler not initialized")


def get_system_container(request: Request):
    """
    Get system container via Dependency Injection.

    Args:
        request: FastAPI request

    Returns:
        System container instance
    """
    # Get container from app state (set during lifespan)
    if hasattr(request.app.state, "container"):
        return request.app.state.container
    raise RuntimeError("Container not initialized")
