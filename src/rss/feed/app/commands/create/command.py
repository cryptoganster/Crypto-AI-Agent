"""CreateSourceCommand: DTO puro para crear fuentes RSS - CQRS simplificado."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateRssFeedCommand:
    """
    DTO puro para crear nueva fuente RSS.

    CQRS simplificado: Un solo objeto inmutable con primitivos.
    Sin abstracciones innecesarias ni command bus.
    """

    source_url: str
    name: str
    description: Optional[str] = None
    is_active: bool = True

    # Configuración opcional para el Source
    fetch_interval_minutes: Optional[int] = None
    max_articles_per_fetch: Optional[int] = None
    timeout_seconds: Optional[int] = None

    def __post_init__(self):
        """Normalización básica post-inicialización. Validaciones se delegan al Validator."""
        # Solo normalizar strings, sin validaciones
        if self.source_url:
            object.__setattr__(self, "source_url", self.source_url.strip())

        if self.name:
            object.__setattr__(self, "name", self.name.strip())

        if self.description:
            normalized_desc = self.description.strip()
            if not normalized_desc:
                object.__setattr__(self, "description", None)
            else:
                object.__setattr__(self, "description", normalized_desc)
