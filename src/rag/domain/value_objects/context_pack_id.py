"""Value Object para identificador único de ContextPack."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContextPackId:
    """
    Value Object para identificador único de ContextPack.

    Usa UUID v4 para garantizar unicidad global.

    Attributes:
        value: UUID del context pack

    Examples:
        >>> pack_id = ContextPackId.generate()
        >>> isinstance(pack_id.value, UUID)
        True
        >>> pack_id2 = ContextPackId.from_string(str(pack_id.value))
        >>> pack_id == pack_id2
        True
    """

    value: UUID

    def __post_init__(self):
        """Valida que el ID sea válido."""
        if not isinstance(self.value, UUID):
            raise TypeError(
                f"ContextPackId value debe ser UUID, recibido: {type(self.value)}"
            )

    @classmethod
    def generate(cls) -> "ContextPackId":
        """
        Genera un nuevo ContextPackId único.

        Returns:
            ContextPackId con UUID v4 generado

        Examples:
            >>> pack_id = ContextPackId.generate()
            >>> len(str(pack_id.value))
            36
        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "ContextPackId":
        """
        Crea ContextPackId desde string UUID.

        Args:
            id_string: String representando un UUID

        Returns:
            ContextPackId

        Raises:
            ValueError: Si el string no es un UUID válido

        Examples:
            >>> pack_id = ContextPackId.from_string("550e8400-e29b-41d4-a716-446655440000")
            >>> str(pack_id.value)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        try:
            uuid_value = UUID(id_string)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"String inválido para UUID: {id_string}") from e

        return cls(value=uuid_value)

    def __str__(self) -> str:
        """Representación en string del ContextPackId."""
        return str(self.value)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ContextPackId('{self.value}')"

    def __hash__(self) -> int:
        """Hash del ContextPackId."""
        return hash(self.value)
