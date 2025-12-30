"""ScrapingStatus Value Object - Estado de scraping."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ScrapingPhase(Enum):
    """Fases del proceso de scraping."""

    IDLE = "idle"
    STARTING = "starting"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass(frozen=True)
class ScrapingStatus:
    """
    Value Object que representa el estado actual de scraping.

    Encapsula las reglas de negocio relacionadas con el proceso de scraping
    y valida las transiciones de estado permitidas.
    """

    phase: ScrapingPhase
    current_scraping_id: Optional[str] = None
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    timeout_seconds: int = 30

    def __post_init__(self):
        """Validaciones de invariantes de negocio."""
        if self.phase != ScrapingPhase.IDLE:
            if not self.current_scraping_id:
                raise ValueError(
                    "current_scraping_id es requerido cuando phase != IDLE"
                )
            if not self.started_at:
                raise ValueError("started_at es requerido cuando phase != IDLE")

        if self.phase == ScrapingPhase.IDLE:
            if self.current_scraping_id:
                raise ValueError(
                    "current_scraping_id debe ser None cuando phase == IDLE"
                )
            if self.started_at:
                raise ValueError("started_at debe ser None cuando phase == IDLE")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser mayor a 0")

    @classmethod
    def idle(cls) -> "ScrapingStatus":
        """Crea un estado de scraping inactivo."""
        return cls(phase=ScrapingPhase.IDLE)

    @classmethod
    def starting(cls, scraping_id: str, timeout_seconds: int = 30) -> "ScrapingStatus":
        """Crea un estado de scraping iniciando."""
        now = datetime.now(timezone.utc)
        return cls(
            phase=ScrapingPhase.STARTING,
            current_scraping_id=scraping_id,
            started_at=now,
            last_activity_at=now,
            timeout_seconds=timeout_seconds,
        )

    def transition_to_scraping(self) -> "ScrapingStatus":
        """Transición a fase de scraping."""
        if not self.can_transition_to_scraping():
            raise ValueError(f"No se puede transicionar de {self.phase} a SCRAPING")

        return ScrapingStatus(
            phase=ScrapingPhase.SCRAPING,
            current_scraping_id=self.current_scraping_id,
            started_at=self.started_at,
            last_activity_at=datetime.now(timezone.utc),
            timeout_seconds=self.timeout_seconds,
        )

    def transition_to_processing(self) -> "ScrapingStatus":
        """Transición a fase de procesamiento."""
        if not self.can_transition_to_processing():
            raise ValueError(f"No se puede transicionar de {self.phase} a PROCESSING")

        return ScrapingStatus(
            phase=ScrapingPhase.PROCESSING,
            current_scraping_id=self.current_scraping_id,
            started_at=self.started_at,
            last_activity_at=datetime.now(timezone.utc),
            timeout_seconds=self.timeout_seconds,
        )

    def transition_to_stopping(self) -> "ScrapingStatus":
        """Transición a fase de detención."""
        if not self.can_transition_to_stopping():
            raise ValueError(f"No se puede transicionar de {self.phase} a STOPPING")

        return ScrapingStatus(
            phase=ScrapingPhase.STOPPING,
            current_scraping_id=self.current_scraping_id,
            started_at=self.started_at,
            last_activity_at=datetime.now(timezone.utc),
            timeout_seconds=self.timeout_seconds,
        )

    def transition_to_idle(self) -> "ScrapingStatus":
        """Transición a estado inactivo (scraping terminado)."""
        if not self.can_transition_to_idle():
            raise ValueError(f"No se puede transicionar de {self.phase} a IDLE")

        return ScrapingStatus.idle()

    # Métodos de validación de transición

    def can_start_new_scraping(self) -> bool:
        """Verifica si se puede iniciar un nuevo scraping."""
        return self.phase == ScrapingPhase.IDLE

    def can_transition_to_scraping(self) -> bool:
        """Verifica si se puede transicionar a scraping."""
        return self.phase == ScrapingPhase.STARTING

    def can_transition_to_processing(self) -> bool:
        """Verifica si se puede transicionar a processing."""
        return self.phase == ScrapingPhase.SCRAPING

    def can_transition_to_stopping(self) -> bool:
        """Verifica si se puede transicionar a stopping."""
        return self.phase in [
            ScrapingPhase.SCRAPING,
            ScrapingPhase.PROCESSING,
        ]

    def can_transition_to_idle(self) -> bool:
        """Verifica si se puede transicionar a idle."""
        return self.phase in [
            ScrapingPhase.STARTING,  # Permitir desde STARTING (fallo al iniciar)
            ScrapingPhase.STOPPING,
            ScrapingPhase.STOPPED,
        ]

    def can_be_cancelled(self) -> bool:
        """Verifica si el scraping actual puede ser cancelado."""
        return self.phase in [
            ScrapingPhase.STARTING,
            ScrapingPhase.SCRAPING,
            ScrapingPhase.PROCESSING,
        ]

    # Propiedades de estado

    @property
    def is_active(self) -> bool:
        """True si hay un scraping en progreso."""
        return self.phase != ScrapingPhase.IDLE

    @property
    def is_idle(self) -> bool:
        """True si no hay scraping en progreso."""
        return self.phase == ScrapingPhase.IDLE

    @property
    def is_busy(self) -> bool:
        """True si está ocupado (scraping o processing)."""
        return self.phase in [
            ScrapingPhase.SCRAPING,
            ScrapingPhase.PROCESSING,
        ]

    @property
    def duration_seconds(self) -> float:
        """Duración en segundos desde el inicio del scraping."""
        if not self.started_at:
            return 0.0
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    @property
    def is_timeout(self) -> bool:
        """True si el scraping ha excedido el timeout."""
        if not self.is_active:
            return False
        return self.duration_seconds > self.timeout_seconds

    @property
    def time_remaining_seconds(self) -> float:
        """Tiempo restante antes del timeout."""
        if not self.is_active:
            return 0.0
        return max(0.0, self.timeout_seconds - self.duration_seconds)

    def __str__(self) -> str:
        if self.is_idle:
            return "ScrapingStatus(IDLE)"
        return f"ScrapingStatus({self.phase.value}, scraping_id={self.current_scraping_id})"
