"""ErrorResponse schema."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Response estándar para errores."""

    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    code: Optional[str] = Field(None, description="Código de error interno")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation error",
                "detail": "Invalid source URL format",
                "code": "VALIDATION_ERROR",
                "timestamp": "2025-10-04T04:00:00Z",
            }
        }
    )
