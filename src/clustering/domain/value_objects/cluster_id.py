"""ClusterId value object para identificar clusters semánticos."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterId:
    """
    Value object para identificador de cluster semántico.

    Representa un identificador único e inmutable para un cluster
    de artículos similares basado en embeddings semánticos.

    Attributes:
        value: UUID como string

    Examples:
        >>> cluster_id = ClusterId.generate()
        >>> str(cluster_id)
        'cluster-...'
        >>> cluster_id2 = ClusterId.from_string(str(cluster_id))
        >>> cluster_id == cluster_id2
        True
    """

    value: str

    def __post_init__(self):
        """Valida el cluster ID."""
        if not self.value:
            raise ValueError("ClusterId value no puede estar vacío")

        if not isinstance(self.value, str):
            raise ValueError("ClusterId value debe ser string")

        # Validar formato si tiene prefijo
        if self.value.startswith("cluster-"):
            uuid_part = self.value[8:]  # Remover "cluster-"
            try:
                uuid.UUID(uuid_part)
            except ValueError:
                raise ValueError(f"ClusterId inválido: {self.value}")

    @classmethod
    def generate(cls) -> "ClusterId":
        """
        Genera un nuevo ClusterId único.

        Returns:
            ClusterId nuevo con UUID generado

        Examples:
            >>> cluster_id = ClusterId.generate()
            >>> cluster_id.value.startswith("cluster-")
            True
        """
        return cls(value=f"cluster-{uuid.uuid4()}")

    @classmethod
    def from_string(cls, value: str) -> "ClusterId":
        """
        Crea ClusterId desde string.

        Args:
            value: String con el ID del cluster

        Returns:
            ClusterId creado desde el string

        Raises:
            ValueError: Si el string es inválido

        Examples:
            >>> cluster_id = ClusterId.from_string("cluster-123e4567-e89b-12d3-a456-426614174000")
            >>> cluster_id.value
            'cluster-123e4567-e89b-12d3-a456-426614174000'
        """
        return cls(value=value)

    def __str__(self) -> str:
        """Retorna representación en string del ClusterId."""
        return self.value

    def __repr__(self) -> str:
        """Retorna representación para debugging."""
        return f"ClusterId(value='{self.value}')"
