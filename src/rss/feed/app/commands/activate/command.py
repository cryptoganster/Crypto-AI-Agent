"""ActivateSourceCommand: DTO puro para activar fuente RSS - CQRS simplificado."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActivateRssFeedCommand:
    """
    DTO puro para activar fuente RSS usando nuevo aggregate Source.

    CQRS simplificado: Solo primitivos, sin abstracciones innecesarias.
    Handler construye VOs desde primitivos.
    """

    # Primitivos (CQRS estricto)
    source_id: str  # SourceId como string (único identificador)
    activated_by: Optional[str] = None
    correlation_id: Optional[str] = None

    # Configuración de activación
    force_activation: bool = False  # Activar aunque tenga problemas de salud
    test_connection: bool = True  # Probar conexión antes de activar
    reset_health_metrics: bool = False  # Resetear métricas de salud al activar
