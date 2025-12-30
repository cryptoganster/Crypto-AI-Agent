"""Value Object para GUID de artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RssArticleGuid:
    """
from __future__ import annotations

    Value Object para GUID único del item RSS.

    El GUID (Globally Unique Identifier) es un identificador único
    proporcionado por el feed RSS para cada item.
    """

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.value:
            raise ValueError("GUID no puede estar vacío")

        if len(self.value.strip()) == 0:
            raise ValueError("GUID no puede ser solo espacios")

        if len(self.value) > 500:
            raise ValueError("GUID no puede exceder 500 caracteres")

        # Normalizar: strip whitespace
        normalized = self.value.strip()
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, guid: str) -> "ArticleGuid":
        """Factory method para crear ArticleGuid."""
        return cls(guid)

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)
