"""
Value Object para duración de timeouts en operaciones de scraping.
Encapsula validación y conversiones de tiempo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeoutDuration:
    """
    Value Object para timeouts de operaciones de scraping.

    Garantiza:
    - Timeout mínimo de 1 segundo (evita timeouts inútiles)
    - Timeout máximo de 300 segundos / 5 minutos (evita cuelgues)
    """

    seconds: int

    # Constantes de timeout predefinidas
    DEFAULT = 30  # Timeout por defecto para sitios normales
    QUICK = 10  # Para sitios rápidos/estáticos
    SLOW = 60  # Para sitios lentos/JS-heavy
    MAX = 300  # Máximo absoluto permitido

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.seconds, int):
            raise TypeError(f"Timeout debe ser int, recibido: {type(self.seconds)}")

        if self.seconds < 1:
            raise ValueError(f"Timeout debe ser al menos 1 segundo: {self.seconds}")

        if self.seconds > self.MAX:
            raise ValueError(
                f"Timeout no puede exceder {self.MAX} segundos: {self.seconds}"
            )

    @classmethod
    def create(cls, seconds: int) -> "TimeoutDuration":
        """Factory method para crear timeout."""
        return cls(seconds)

    @classmethod
    def default(cls) -> "TimeoutDuration":
        """Crea timeout con valor por defecto (30s)."""
        return cls(cls.DEFAULT)

    @classmethod
    def quick(cls) -> "TimeoutDuration":
        """Crea timeout rápido para sitios estáticos (10s)."""
        return cls(cls.QUICK)

    @classmethod
    def slow(cls) -> "TimeoutDuration":
        """Crea timeout lento para sitios JS-heavy (60s)."""
        return cls(cls.SLOW)

    def to_milliseconds(self) -> int:
        """Convierte a milisegundos (útil para Playwright)."""
        return self.seconds * 1000

    def to_minutes(self) -> float:
        """Convierte a minutos."""
        return self.seconds / 60.0

    def is_quick(self) -> bool:
        """Verifica si es un timeout rápido (<= 15s)."""
        return self.seconds <= 15

    def is_slow(self) -> bool:
        """Verifica si es un timeout lento (>= 45s)."""
        return self.seconds >= 45

    def with_buffer(self, buffer_seconds: int = 5) -> "TimeoutDuration":
        """
        Crea nuevo timeout agregando buffer.

        Args:
            buffer_seconds: Segundos adicionales a agregar

        Returns:
            Nuevo TimeoutDuration con buffer agregado
        """
        new_seconds = min(self.seconds + buffer_seconds, self.MAX)
        return TimeoutDuration(new_seconds)

    def __str__(self) -> str:
        return f"{self.seconds}s"

    def __int__(self) -> int:
        return self.seconds

    def __repr__(self) -> str:
        return f"TimeoutDuration(seconds={self.seconds})"
