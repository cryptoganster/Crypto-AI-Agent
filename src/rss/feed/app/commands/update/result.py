"""UpdateSourceResult: Resultado del comando UpdateSource."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UpdateRssFeedResult:
    """Resultado de la operación UpdateSource."""

    # Estado de la operación
    success: bool
    message: str
    error_code: Optional[str] = None

    # Datos de la operación
    source_id: Optional[str] = None
    old_details: Optional[Dict[str, Any]] = None
    new_details: Optional[Dict[str, Any]] = None
    config_updated: bool = False

    @classmethod
    def success_result(
        cls,
        source_id: str,
        old_details: Dict[str, Any],
        new_details: Dict[str, Any],
        config_updated: bool = False,
    ) -> "UpdateRssFeedResult":
        """Resultado exitoso."""
        return cls(
            success=True,
            message="Source actualizado exitosamente",
            source_id=source_id,
            old_details=old_details,
            new_details=new_details,
            config_updated=config_updated,
        )

    @classmethod
    def failure_result(
        cls,
        source_id: Optional[str] = None,
        message: str = "Error al actualizar source",
        error_code: str = "UPDATE_FAILED",
    ) -> "UpdateRssFeedResult":
        """Resultado fallido."""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            source_id=source_id,
        )

    @classmethod
    def source_not_found(cls, source_id: str) -> "UpdateRssFeedResult":
        """Source no encontrado."""
        return cls(
            success=False,
            message=f"Source con ID {source_id} no encontrado",
            error_code="SOURCE_NOT_FOUND",
            source_id=source_id,
        )

    @classmethod
    def invalid_configuration(
        cls, source_id: str, validation_errors: str
    ) -> "UpdateRssFeedResult":
        """Configuración inválida."""
        return cls(
            success=False,
            message=f"Configuración inválida: {validation_errors}",
            error_code="INVALID_CONFIG",
            source_id=source_id,
        )
