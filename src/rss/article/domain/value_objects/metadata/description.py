"""Value Object para descripción de artículo."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RssArticleDescription:
    """
from __future__ import annotations

    Value Object para descripción/excerpt del artículo.

    Representa una descripción corta o excerpt del artículo,
    típicamente extraído del feed RSS o generado automáticamente.
    """

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if self.value is None:
            raise ValueError(
                "Descripción no puede ser None (usar empty string si vacío)"
            )

        # Permitir descripción vacía
        if len(self.value.strip()) == 0:
            object.__setattr__(self, "value", "")
        else:
            if len(self.value) > 2000:
                raise ValueError("Descripción no puede exceder 2000 caracteres")

            # Normalizar espacios
            import re

            normalized = re.sub(r"\s+", " ", self.value.strip())
            object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, description: Optional[str]) -> Optional["ArticleDescription"]:
        """Factory method para crear descripción (retorna None si vacío)."""
        if not description or not description.strip():
            return None
        return cls(description)

    @classmethod
    def empty(cls) -> "ArticleDescription":
        """Crea descripción vacía."""
        return cls("")

    def truncate(self, max_length: int = 300, suffix: str = "...") -> str:
        """Trunca la descripción a una longitud máxima con sufijo."""
        if len(self.value) <= max_length:
            return self.value
        return self.value[:max_length] + suffix

    def is_empty(self) -> bool:
        """Verifica si la descripción está vacía."""
        return len(self.value.strip()) == 0

    def get_word_count(self) -> int:
        """Obtiene conteo de palabras."""
        if self.is_empty():
            return 0
        return len(self.value.split())

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __bool__(self) -> bool:
        """Permite usar en contextos booleanos."""
        return not self.is_empty()
