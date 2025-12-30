"""ScrapingTimestamps Value Object - Timestamps del ciclo de vida."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class ScrapingTimestamps:
    """
    Timestamps del ciclo de vida de Scraping.

    Agrupa todos los timestamps relacionados con el ciclo de vida:
    - created_at: Cuándo se creó la sesión
    - updated_at: Última actualización
    - completed_at: Cuándo se completó (None si aún no)

    Este VO es inmutable. Cada cambio retorna una nueva instancia.
    """

    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Valida los timestamps."""
        if self.created_at.tzinfo is None:
            raise ValueError("created_at debe tener timezone")

        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at debe tener timezone")

        if self.completed_at is not None and self.completed_at.tzinfo is None:
            raise ValueError("completed_at debe tener timezone")

        if self.updated_at < self.created_at:
            raise ValueError("updated_at no puede ser anterior a created_at")

        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at no puede ser anterior a created_at")

    @classmethod
    def create_new(cls) -> "ScrapingTimestamps":
        """
        Crea timestamps para una nueva sesión.

        Returns:
            ScrapingTimestamps con created_at y updated_at en now
        """
        now = datetime.now(timezone.utc)
        return cls(
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

    def with_updated(self) -> "ScrapingTimestamps":
        """
        Retorna nueva instancia con updated_at actualizado a now.

        Returns:
            Nueva ScrapingTimestamps con updated_at = now
        """
        return ScrapingTimestamps(
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            completed_at=self.completed_at,
        )

    def with_completed(self) -> "ScrapingTimestamps":
        """
        Retorna nueva instancia marcada como completada.

        Actualiza tanto updated_at como completed_at a now.

        Returns:
            Nueva ScrapingTimestamps con completed_at = now

        Raises:
            ValueError: Si ya está completada
        """
        if self.completed_at is not None:
            raise ValueError("La sesión ya está completada")

        now = datetime.now(timezone.utc)
        return ScrapingTimestamps(
            created_at=self.created_at,
            updated_at=now,
            completed_at=now,
        )

    def is_completed(self) -> bool:
        """
        Verifica si la sesión está completada.

        Returns:
            True si completed_at no es None
        """
        return self.completed_at is not None

    def get_duration_seconds(self) -> Optional[float]:
        """
        Calcula la duración de la sesión en segundos.

        Returns:
            Duración en segundos si está completada, None si no
        """
        if self.completed_at is None:
            return None

        duration = self.completed_at - self.created_at
        return duration.total_seconds()

    def __str__(self) -> str:
        """Representación string."""
        status = "completed" if self.is_completed() else "in progress"
        return f"ScrapingTimestamps({status}, created={self.created_at.isoformat()})"
