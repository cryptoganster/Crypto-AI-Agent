"""Source ID Value Object - Ubicación canónica."""

from typing import Any, Dict, Type
from uuid import UUID, uuid4

from src.shared.kernel import IValueObject


class RssFeedId(IValueObject):
    """
    ID único para Source entity.

    Esta es la ubicación canónica de SourceId.
    Todos los imports deben usar: from src.rss.feed.domain.value_objects import SourceId
    """

    __slots__ = ("_value",)

    def __init__(self, value):
        """Inicializa SourceId convirtiendo UUID a string si es necesario."""
        # Convertir UUID a string automáticamente
        if isinstance(value, UUID):
            value = str(value)
        elif not isinstance(value, str):
            value = str(value)

        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        """Retorna el valor del ID como string."""
        return self._value

    @classmethod
    def generate(cls) -> "SourceId":
        """Genera un nuevo SourceId aleatorio."""
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        """Retorna el valor como string."""
        return self._value

    def __repr__(self) -> str:
        """Representación del objeto."""
        return f"SourceId(value='{self._value}')"

    def __eq__(self, other: object) -> bool:
        """Compara dos SourceId por valor."""
        if not isinstance(other, SourceId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash basado en el valor."""
        return hash(self._value)

    def __setattr__(self, name, value):
        """Previene modificación después de la inicialización (immutable)."""
        raise AttributeError("SourceId es inmutable")

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el Source ID a diccionario."""
        return {"value": self._value}

    @classmethod
    def from_string(cls: Type["SourceId"], value: str) -> "SourceId":
        """Crea un Source ID desde string."""
        return cls(value=value)

    @classmethod
    def from_dict(cls: Type["SourceId"], data: Dict[str, Any]) -> "SourceId":
        """Deserializa el Source ID desde diccionario."""
        return cls(value=data["value"])


# Alias para compatibilidad hacia atrás
SourceId = RssFeedId
