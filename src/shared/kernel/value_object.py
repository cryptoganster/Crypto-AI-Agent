"""Interface base para Value Objects en Domain-Driven Design."""

from abc import ABC, abstractmethod
from typing import Any


class IValueObject(ABC):
    """
    Interface base para Value Objects en DDD.

    Los Value Objects son inmutables y su igualdad se basa en sus valores,
    no en identidad. No tienen identidad conceptual y son intercambiables.
    """

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """
        Igualdad basada en valores, no en identidad.
        Dos value objects son iguales si todos sus atributos son iguales.
        """
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """
        Hash basado en valores para permitir uso en sets y como keys.
        Debe ser consistente con __eq__.
        """
        pass
