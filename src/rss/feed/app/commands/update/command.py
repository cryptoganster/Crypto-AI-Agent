"""UpdateSourceCommand: DTO puro para actualizar Source aggregate - CQRS simplificado."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UpdateRssFeedCommand:
    """
    DTO puro para actualizar detalles y configuración de Source.

    CQRS simplificado con arquitectura independiente:
    - Actualiza Source aggregate específicamente
    - Maneja detalles básicos: nombre, descripción, configuración
    - Separado de fetch operations (que va en FetchSession)
    """

    # Primitivos (CQRS estricto)
    source_id: str  # SourceId como string
    correlation_id: Optional[str] = None
    updated_by: Optional[str] = None

    # Detalles de Source (opcionales - solo se actualizan si se proveen)
    name: Optional[str] = None
    description: Optional[str] = None

    # Configuración específica de Source
    source_config: Optional[Dict[str, Any]] = None

    # Control de actualización
    apply_immediately: bool = True
    validate_config: bool = True
