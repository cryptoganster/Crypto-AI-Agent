"""ValidationErrorDetail schema."""

from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorDetail(BaseModel):
    """Detalle de error de validación."""

    field: str = Field(..., description="Campo que falló la validación")
    message: str = Field(..., description="Mensaje de error")
    type: str = Field(..., description="Tipo de error de validación")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "type": "value_error.email",
            }
        }
    )
