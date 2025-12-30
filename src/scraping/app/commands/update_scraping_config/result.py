"""Result object para UpdateScrapingConfigCommand."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UpdateScrapingConfigResult:
    """
    Result object para operación de actualización de configuración.

    Attributes:
        success: Indica si la actualización fue exitosa
        source_id: ID de la fuente actualizada
        old_config: Configuración anterior
        new_config: Nueva configuración aplicada
        changes_applied: Indica si los cambios fueron aplicados
        error_message: Mensaje de error si falló
        error_code: Código de error si falló
    """

    success: bool
    source_id: str

    # Configuraciones
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None
    changes_applied: bool = False

    # Error info
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        source_id: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        changes_applied: bool = True,
    ) -> "UpdateScrapingConfigResult":
        """Crea resultado exitoso."""
        return cls(
            success=True,
            source_id=source_id,
            old_config=old_config,
            new_config=new_config,
            changes_applied=changes_applied,
        )

    @classmethod
    def failure_result(
        cls,
        source_id: str,
        message: str,
        error_code: str,
    ) -> "UpdateScrapingConfigResult":
        """Crea resultado fallido."""
        return cls(
            success=False,
            source_id=source_id,
            error_message=message,
            error_code=error_code,
        )

    @classmethod
    def scraping_not_found(cls, source_id: str) -> "UpdateScrapingConfigResult":
        """Crea resultado cuando no se encuentra la sesión de scraping."""
        return cls(
            success=False,
            source_id=source_id,
            error_message=f"No se encontró sesión de scraping para la fuente {source_id}",
            error_code="SCRAPING_SESSION_NOT_FOUND",
        )
