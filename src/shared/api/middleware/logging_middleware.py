"""Logging middleware para FastAPI."""

import time
import uuid
from typing import Callable

from fastapi import Request


async def logging_middleware(request: Request, call_next: Callable):
    """
    Middleware para logging estructurado de requests.

    Registra:
    - Request ID único
    - Método HTTP y path
    - Duración de la request
    - Status code de response
    """
    # Generar request ID único
    request_id = str(uuid.uuid4())

    # Agregar request_id al state
    request.state.request_id = request_id

    # Timestamp de inicio
    start_time = time.time()

    # Obtener logger del sistema si está disponible
    logger = None
    if hasattr(request.app.state, "container"):
        logger = request.app.state.container.shared.logger.bind(
            component="FastAPI",
            request_id=request_id,
        )

    # Log de request
    if logger:
        logger.info(
            f"→ {request.method} {request.url.path}",
            method=request.method,
            path=str(request.url.path),
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
        )

    # Procesar request
    response = await call_next(request)

    # Calcular duración
    duration = time.time() - start_time

    # Agregar headers de metadata
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.3f}s"

    # Log de response
    if logger:
        logger.info(
            f"← {response.status_code} {request.method} {request.url.path}",
            status_code=response.status_code,
            duration_seconds=round(duration, 3),
        )

    return response
