"""HealthResponse schema."""

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Response para health check endpoints."""

    status: str = Field(..., description="Estado del servicio")
    version: str = Field(..., description="Versión de la API")
    uptime: Optional[float] = Field(None, description="Tiempo activo en segundos")
    components: Optional[Dict[str, str]] = Field(
        None, description="Estado de componentes"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "components": {"database": "healthy", "cache": "healthy"},
            }
        }
    )
