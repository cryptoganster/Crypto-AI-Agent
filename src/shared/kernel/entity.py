"""Interface base para Entidades en Domain-Driven Design."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

EntityId = TypeVar("EntityId")


class IEntity(ABC, Generic[EntityId]):
    """
    Interface base para todas las entidades del dominio.

    Una entidad tiene identidad única y su igualdad se basa en su ID,
    no en sus atributos. Siguiendo principios de DDD.
    """

    @property
    @abstractmethod
    def id(self) -> EntityId:
        """ID único de la entidad."""
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Timestamp de creación de la entidad."""
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """Timestamp de última actualización de la entidad."""
        pass

    def __eq__(self, other: Any) -> bool:
        """
        Igualdad basada en identidad, no en atributos.
        Dos entidades son iguales si tienen el mismo ID y tipo.
        """
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash basado en ID para permitir uso en sets y como keys de dict."""
        return hash((type(self).__name__, self.id))

    def __repr__(self) -> str:
        """Representación string para debugging."""
        return f"{type(self).__name__}(id={self.id})"
