"""ScrapingError Value Object para errores de scraping."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.rss.feed.domain.value_objects import SourceId


@dataclass(frozen=True)
class ScrapingError:
    """
    Value Object inmutable para representar errores durante scraping.

    Encapsula información sobre errores que ocurren durante el proceso
    de scraping de un source, incluyendo tipo de error, mensaje, timestamp
    y si es recuperable.

    Attributes:
        source_id: ID del source donde ocurrió el error
        error_type: Tipo de error (e.g., "timeout", "connection_error", "parse_error")
        error_message: Mensaje descriptivo del error
        occurred_at: Timestamp cuando ocurrió el error
        is_recoverable: Si el error es recuperable (puede reintentarse)
        http_status_code: Código HTTP si aplica (opcional)

    Example:
        >>> error = ScrapingError(
        ...     source_id=SourceId("src-123"),
        ...     error_type="timeout",
        ...     error_message="Connection timeout after 30s",
        ...     occurred_at=datetime.utcnow(),
        ...     is_recoverable=True,
        ...     http_status_code=None
        ... )
        >>> error.is_recoverable
        True
    """

    source_id: SourceId
    error_type: str
    error_message: str
    occurred_at: datetime
    is_recoverable: bool = True
    http_status_code: Optional[int] = None

    def __post_init__(self):
        """Valida los valores del error."""
        if not self.error_type or not self.error_type.strip():
            raise ValueError("error_type no puede estar vacío")

        if not self.error_message or not self.error_message.strip():
            raise ValueError("error_message no puede estar vacío")

        if self.http_status_code is not None:
            if not 100 <= self.http_status_code <= 599:
                raise ValueError(
                    f"http_status_code debe estar entre 100 y 599, "
                    f"recibido: {self.http_status_code}"
                )

    def to_dict(self) -> dict:
        """
        Serializa el error a diccionario.

        Returns:
            Diccionario con la información del error
        """
        return {
            "source_id": str(self.source_id),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "occurred_at": self.occurred_at.isoformat(),
            "is_recoverable": self.is_recoverable,
            "http_status_code": self.http_status_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapingError":
        """
        Crea una instancia desde un diccionario.

        Args:
            data: Diccionario con los valores del error

        Returns:
            Nueva instancia de ScrapingError
        """
        return cls(
            source_id=SourceId(data["source_id"]),
            error_type=data["error_type"],
            error_message=data["error_message"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            is_recoverable=data.get("is_recoverable", True),
            http_status_code=data.get("http_status_code"),
        )

    def is_client_error(self) -> bool:
        """
        Verifica si es un error del cliente (4xx).

        Returns:
            True si es error 4xx
        """
        return self.http_status_code is not None and 400 <= self.http_status_code < 500

    def is_server_error(self) -> bool:
        """
        Verifica si es un error del servidor (5xx).

        Returns:
            True si es error 5xx
        """
        return self.http_status_code is not None and 500 <= self.http_status_code < 600
