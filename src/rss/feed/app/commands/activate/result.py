"""Results para ActivateSource command."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class ActivateRssFeedResult:
    """Result del comando ActivateSource usando Source aggregate."""

    # Campos obligatorios (sin valores por defecto)
    success: bool
    source_id: str

    # Campos opcionales (con valores por defecto)
    source_name: Optional[str] = field(default=None)
    source_url: Optional[str] = field(default=None)
    message: str = ""
    error_code: Optional[str] = field(default=None)
    activated_at: Optional[datetime] = field(default=None)
    health_metrics_reset: bool = False
    connection_tested: bool = False

    @classmethod
    def success_result(
        cls,
        source_id: str,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        health_metrics_reset: bool = False,
        connection_tested: bool = False,
    ) -> "ActivateSourceResult":
        """Factory method para resultado exitoso."""
        return cls(
            success=True,
            source_id=source_id,
            source_name=source_name,
            source_url=source_url,
            message=f"Fuente RSS '{source_name}' activada exitosamente",
            activated_at=datetime.now(timezone.utc),
            health_metrics_reset=health_metrics_reset,
            connection_tested=connection_tested,
        )

    @classmethod
    def failure_result(
        cls,
        source_id: str,
        message: str,
        error_code: Optional[str] = None,
    ) -> "ActivateSourceResult":
        """Factory method para resultado fallido."""
        return cls(
            success=False,
            source_id=source_id,
            message=message,
            error_code=error_code,
        )

    @classmethod
    def source_not_found(cls, source_id: str) -> "ActivateSourceResult":
        """Factory method para fuente no encontrada."""
        return cls.failure_result(
            source_id=source_id,
            message=f"Fuente RSS con ID {source_id} no encontrada",
            error_code="SOURCE_NOT_FOUND",
        )

    @classmethod
    def source_already_active(cls, source_id: str) -> "ActivateSourceResult":
        """Factory method para fuente ya activa."""
        return cls.failure_result(
            source_id=source_id,
            message=f"Fuente RSS {source_id} ya está activa. Use force_activation=True para reactivar.",
            error_code="SOURCE_ALREADY_ACTIVE",
        )

    @classmethod
    def connection_test_failed(
        cls, source_id: str, error_details: str
    ) -> "ActivateSourceResult":
        """Factory method para test de conexión fallido."""
        return cls.failure_result(
            source_id=source_id,
            message=f"Test de conexión falló para fuente {source_id}: {error_details}",
            error_code="CONNECTION_TEST_FAILED",
        )
