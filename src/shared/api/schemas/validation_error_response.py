"""ValidationErrorResponse schema."""

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field

from .validation_error_detail import ValidationErrorDetail


class ValidationErrorResponse(BaseModel):
    """Response para errores de validación."""

    error: str = Field("Validation Error", description="Tipo de error")
    details: List[ValidationErrorDetail] = Field(
        ..., description="Lista de errores de validación"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
