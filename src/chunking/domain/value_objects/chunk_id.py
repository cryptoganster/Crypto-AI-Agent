"""Value Object para identificador único de ContentChunk."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ChunkId:
    """
    Value Object para identificador único de ContentChunk.

    Usa UUID v4 para garantizar unicidad global.

    Attributes:
        value: UUID del chunk

    Examples:
        >>> chunk_id = ChunkId.generate()
        >>> isinstance(chunk_id.value, UUID)
        True
        >>> chunk_id2 = ChunkId.from_string(str(chunk_id.value))
        >>> chunk_id == chunk_id2
        True
    """

    value: UUID

    def __post_init__(self):
        """Valida que el ID sea válido."""
        if not isinstance(self.value, UUID):
            raise TypeError(
                f"ChunkId value debe ser UUID, recibido: {type(self.value)}"
            )

    @classmethod
    def generate(cls) -> "ChunkId":
        """
        Genera un nuevo ChunkId único.

        Returns:
            ChunkId con UUID v4 generado

        Examples:
            >>> chunk_id = ChunkId.generate()
            >>> len(str(chunk_id.value))
            36
        """
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "ChunkId":
        """
        Crea ChunkId desde string UUID.

        Args:
            id_string: String representando un UUID

        Returns:
            ChunkId

        Raises:
            ValueError: Si el string no es un UUID válido

        Examples:
            >>> chunk_id = ChunkId.from_string("550e8400-e29b-41d4-a716-446655440000")
            >>> str(chunk_id.value)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        try:
            uuid_value = UUID(id_string)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"String inválido para UUID: {id_string}") from e

        return cls(value=uuid_value)

    def __str__(self) -> str:
        """Representación en string del ChunkId."""
        return str(self.value)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ChunkId('{self.value}')"

    def __hash__(self) -> int:
        """Hash del ChunkId."""
        return hash(self.value)
