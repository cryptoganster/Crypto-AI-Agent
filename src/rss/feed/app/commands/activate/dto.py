"""DTOs para ActivateSource command."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class ActivateSourceRequestDto:
    """DTO de entrada para activar fuente RSS usando Source aggregate."""

    # Campos obligatorios
    source_id: str  # SourceId como string

    # Campos opcionales
    activated_by: Optional[str] = field(default=None)
    force_activation: bool = False
    reset_health_metrics: bool = True
    test_connection: bool = True
    correlation_id: Optional[str] = field(default=None)
    activation_reason: Optional[str] = field(default=None)


@dataclass(frozen=True)
class ActivateSourceResponseDto:
    """DTO de respuesta de activación de fuente usando Source aggregate."""

    success: bool
    source_id: str
    source_name: str
    source_url: str
    was_previously_active: bool
    activated_at: Optional[datetime] = field(default=None)
    message: str = ""
    previous_status: Optional[str] = field(default=None)
    health_metrics_reset: bool = False
    connection_tested: bool = False
    connection_test_result: Optional[dict] = field(default=None)
    health_score_before: Optional[float] = field(default=None)
    health_score_after: Optional[float] = field(default=None)
    last_successful_fetch: Optional[datetime] = field(default=None)


@dataclass(frozen=True)
class SourceActivationDetailsDto:
    """DTO para detalles de activación de fuente."""

    source_id: str
    source_name: str
    source_url: str
    current_status: str
    health_score: Optional[float] = field(default=None)
    last_fetch: Optional[datetime] = field(default=None)
    fetch_count: int = 0
