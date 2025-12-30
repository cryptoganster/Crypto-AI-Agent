"""Value Object para fecha de publicación de artículo."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RssArticlePubDate:
    """
from __future__ import annotations

    Value Object para fecha de publicación del item RSS.

    Encapsula la fecha de publicación proporcionada por el feed RSS.
    """

    value: datetime

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.value, datetime):
            raise TypeError("pub_date debe ser datetime")

        # Asegurar que tenga timezone (UTC si no tiene)
        if self.value.tzinfo is None:
            normalized = self.value.replace(tzinfo=timezone.utc)
            object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, pub_date: datetime) -> "ArticlePubDate":
        """Factory method para crear ArticlePubDate."""
        return cls(pub_date)

    @classmethod
    def now(cls) -> "ArticlePubDate":
        """Crea ArticlePubDate con fecha actual."""
        return cls(datetime.now(timezone.utc))

    def is_future(self) -> bool:
        """Verifica si la fecha es futura."""
        now = datetime.now(timezone.utc)
        return self.value > now

    def is_past(self) -> bool:
        """Verifica si la fecha es pasada."""
        now = datetime.now(timezone.utc)
        return self.value < now

    def age_in_days(self) -> int:
        """Retorna la edad en días desde la publicación."""
        now = datetime.now(timezone.utc)
        delta = now - self.value
        return delta.days

    def to_iso_string(self) -> str:
        """Convierte a string ISO 8601."""
        return self.value.isoformat()

    def __str__(self) -> str:
        return self.value.isoformat()
