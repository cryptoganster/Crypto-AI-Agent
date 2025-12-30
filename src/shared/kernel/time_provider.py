"""Interface para abstracción de time provider.

Permite inyección de dependencias para manejo de tiempo en el dominio.
Ubicado en shared kernel por ser una abstracción cross-cutting.
"""

from datetime import datetime, timezone
from typing import Protocol


class ITimeProvider(Protocol):
    """
    Interface para proveedores de tiempo.

    Permite abstraer la obtención de timestamps para:
    - Testing con tiempo controlado/mockeable
    - Diferentes zonas horarias si es necesario
    - Cumplir con Dependency Inversion Principle

    Example:
        >>> class MockTimeProvider:
        ...     def utc_now(self) -> datetime:
        ...         return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        ...     def now(self) -> datetime:
        ...         return datetime(2024, 1, 1, 12, 0, 0)
        >>>
        >>> service = SomeService(time_provider=MockTimeProvider())
    """

    def utc_now(self) -> datetime:
        """Obtiene timestamp UTC actual."""
        ...

    def now(self) -> datetime:
        """Obtiene timestamp local actual."""
        ...


class SystemTimeProvider:
    """
    Implementación por defecto usando tiempo del sistema.

    Para uso en producción. Retorna timestamps reales del sistema.
    """

    def utc_now(self) -> datetime:
        """Obtiene timestamp UTC actual del sistema."""
        return datetime.now(timezone.utc)

    def now(self) -> datetime:
        """Obtiene timestamp local actual del sistema."""
        return datetime.now()
