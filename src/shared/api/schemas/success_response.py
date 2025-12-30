"""SuccessResponse schema."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    """Response estándar para operaciones exitosas."""

    success: bool = Field(True, description="Indica éxito de la operación")
    message: str = Field(..., description="Mensaje descriptivo")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123e4567-e89b-12d3-a456-426614174000"},
            }
        }
    )
