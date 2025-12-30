"""UpdateScrapingConfigCommand: DTO para actualizar configuración de scraping."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UpdateScrapingConfigCommand:
    """
    DTO para actualizar configuración de scraping de una fuente.

    Actualiza la configuración de scraping en el aggregate Scraping asociado
    a una fuente específica.

    Attributes:
        source_id: ID de la fuente cuya configuración se actualizará
        scraping_config: Nueva configuración de scraping como primitivos
        correlation_id: ID de correlación para tracking
        updated_by: Usuario/sistema que realiza la actualización
        apply_immediately: Aplicar cambios inmediatamente
        validate_config: Validar configuración antes de aplicar
    """

    # Identificador requerido
    source_id: str

    # Nueva configuración
    scraping_config: Dict[str, Any]

    # Metadatos
    correlation_id: Optional[str] = None
    updated_by: Optional[str] = None

    # Control de actualización
    apply_immediately: bool = True
    validate_config: bool = True
