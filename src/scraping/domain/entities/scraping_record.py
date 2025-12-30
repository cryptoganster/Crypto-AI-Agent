"""ScrapingRecord Entity - Registro interno de operaciones de scraping dentro de Scraping aggregate."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from src.shared.kernel import IEntity


@dataclass
class ScrapingId:
    """ID único para un ScrapingRecord."""

    value: str

    @classmethod
    def generate(cls) -> "ScrapingId":
        """Genera un nuevo ScrapingId único."""
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScrapingId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class ScrapingRecordStatus:
    """Estado de un ScrapingRecord."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

    value: str

    @classmethod
    def started(cls) -> "ScrapingRecordStatus":
        return cls(value=cls.STARTED)

    @classmethod
    def completed(cls) -> "ScrapingRecordStatus":
        return cls(value=cls.COMPLETED)

    @classmethod
    def failed(cls) -> "ScrapingRecordStatus":
        return cls(value=cls.FAILED)

    def is_started(self) -> bool:
        return self.value == self.STARTED

    def is_completed(self) -> bool:
        return self.value == self.COMPLETED

    def is_failed(self) -> bool:
        return self.value == self.FAILED

    def __str__(self) -> str:
        return self.value


class ScrapingRecord(IEntity):
    """
    Entity que representa un registro de scraping dentro del Scraping aggregate.

    Esta entity NO es un aggregate root, sino una entity interna que mantiene
    el historial de operaciones de scraping de un Source específico.
    """

    def __init__(self, scraped_by: Optional[str] = None):
        """
        Inicializa un nuevo ScrapingRecord.

        Args:
            scraped_by: Usuario o sistema que inició el scraping
        """
        self._id: ScrapingId = ScrapingId.generate()
        self._status: ScrapingRecordStatus = ScrapingRecordStatus.started()
        self._started_at: datetime = datetime.now(timezone.utc)
        self._completed_at: Optional[datetime] = None
        self._articles_found: int = 0
        self._articles_new: int = 0
        self._response_time_ms: Optional[float] = None
        self._error_message: Optional[str] = None
        self._scraped_by: Optional[str] = scraped_by

    @property
    def id(self) -> ScrapingId:
        """ID único del scraping record."""
        return self._id

    @property
    def status(self) -> ScrapingRecordStatus:
        """Estado actual del scraping."""
        return self._status

    @property
    def started_at(self) -> datetime:
        """Timestamp de inicio del scraping."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Timestamp de completación del scraping."""
        return self._completed_at

    @property
    def articles_found(self) -> int:
        """Total de artículos encontrados en el scraping."""
        return self._articles_found

    @property
    def articles_new(self) -> int:
        """Artículos nuevos encontrados en el scraping."""
        return self._articles_new

    @property
    def response_time_ms(self) -> Optional[float]:
        """Tiempo de respuesta en milisegundos."""
        return self._response_time_ms

    @property
    def error_message(self) -> Optional[str]:
        """Mensaje de error si el scraping falló."""
        return self._error_message

    @property
    def scraped_by(self) -> Optional[str]:
        """Usuario o sistema que inició el scraping."""
        return self._scraped_by

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación (mismo que started_at)."""
        return self._started_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización."""
        return self._completed_at or self._started_at

    @property
    def duration_ms(self) -> Optional[float]:
        """Duración total del scraping en milisegundos."""
        if self._completed_at is None:
            return None
        return (self._completed_at - self._started_at).total_seconds() * 1000

    def complete(
        self,
        articles_found: int,
        articles_new: int = 0,
        response_time_ms: Optional[float] = None,
    ) -> None:
        """
        Marca el scraping como completado exitosamente.

        Args:
            articles_found: Total de artículos encontrados
            articles_new: Artículos nuevos (no duplicados)
            response_time_ms: Tiempo de respuesta del RSS feed

        Raises:
            ValueError: Si el scraping ya fue completado o falló
        """
        if not self._status.is_started():
            raise ValueError(f"No se puede completar scraping en estado {self._status}")

        self._status = ScrapingRecordStatus.completed()
        self._completed_at = datetime.now(timezone.utc)
        self._articles_found = articles_found
        self._articles_new = articles_new
        self._response_time_ms = response_time_ms

    def fail(self, error_message: str) -> None:
        """
        Marca el scraping como fallido.

        Args:
            error_message: Descripción del error

        Raises:
            ValueError: Si el scraping ya fue completado o falló
        """
        if not self._status.is_started():
            raise ValueError(f"No se puede fallar scraping en estado {self._status}")

        self._status = ScrapingRecordStatus.failed()
        self._completed_at = datetime.now(timezone.utc)
        self._error_message = error_message

    def is_successful(self) -> bool:
        """Verifica si el scraping fue exitoso."""
        return self._status.is_completed()

    def is_in_progress(self) -> bool:
        """Verifica si el scraping está en progreso."""
        return self._status.is_started()

    def __str__(self) -> str:
        return f"ScrapingRecord(id={self._id}, status={self._status}, started_at={self._started_at})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScrapingRecord):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
