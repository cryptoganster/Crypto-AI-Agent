"""Error handler middleware para FastAPI."""

import traceback
from typing import Callable

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.api.schemas import (
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)


async def error_handler_middleware(request: Request, call_next: Callable):
    """
    Middleware global para manejo de errores.

    Captura excepciones y retorna responses JSON estructuradas.
    """
    try:
        response = await call_next(request)
        return response

    except RequestValidationError as exc:
        # Errores de validación de Pydantic
        errors = []
        for error in exc.errors():
            errors.append(
                ValidationErrorDetail(
                    field=".".join(str(x) for x in error["loc"]),
                    message=error["msg"],
                    type=error["type"],
                )
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ValidationErrorResponse(
                error="Validation Error",
                details=errors,
            ).model_dump(),
        )

    except StarletteHTTPException as exc:
        # Errores HTTP estándar
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.detail or "HTTP Error",
                detail=str(exc.detail) if exc.detail else "HTTP Error",
                code=f"HTTP_{exc.status_code}",
            ).model_dump(),
        )

    except Exception as exc:
        # Errores no esperados
        error_detail = str(exc)
        error_traceback = traceback.format_exc()

        # Log del error
        if hasattr(request.app.state, "container"):
            logger = request.app.state.container.shared.logger
            logger.error(
                "Unhandled error",
                error=error_detail,
                traceback=error_traceback,
            )
        else:
            print(f"Unhandled error: {error_detail}")
            print(error_traceback)

        # En development mostrar detalles, en production ocultar
        show_details = False
        if hasattr(request.app.state, "container"):
            show_details = request.app.state.container.config.is_development

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal Server Error",
                detail=error_detail if show_details else "An unexpected error occurred",
                code="INTERNAL_ERROR",
            ).model_dump(),
        )


def map_domain_exception_to_http_status(exc: Exception) -> int:
    """
    Mapea excepciones de dominio a códigos HTTP.

    Args:
        exc: Excepción capturada

    Returns:
        Código de estado HTTP apropiado
    """
    exception_name = exc.__class__.__name__

    # Mapeo de excepciones comunes
    mapping = {
        "ValidationException": status.HTTP_400_BAD_REQUEST,
        "NotFoundException": status.HTTP_404_NOT_FOUND,
        "DuplicateException": status.HTTP_409_CONFLICT,
        "UnauthorizedException": status.HTTP_401_UNAUTHORIZED,
        "ForbiddenException": status.HTTP_403_FORBIDDEN,
    }

    return mapping.get(exception_name, status.HTTP_500_INTERNAL_SERVER_ERROR)
