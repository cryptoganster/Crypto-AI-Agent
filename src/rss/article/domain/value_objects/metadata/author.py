"""
Value Object para autor de artículos RSS.
Encapsula validación y normalización de autores.
"""
from __future__ import annotations


import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RssArticleAuthor:
    """Value Object para autores de artículos RSS."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.value:
            raise ValueError("Autor no puede estar vacío")

        if len(self.value.strip()) == 0:
            raise ValueError("Autor no puede ser solo espacios")

        if len(self.value) > 200:
            raise ValueError("Nombre de autor no puede exceder 200 caracteres")

        # Normalizar: eliminar espacios extra
        normalized = re.sub(r"\s+", " ", self.value.strip())
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, author: Optional[str]) -> Optional["ArticleAuthor"]:
        """Factory method para crear autor (retorna None si vacío)."""
        if not author or not author.strip():
            return None
        return cls(author)

    def get_initials(self) -> str:
        """Obtiene las iniciales del autor.

        Returns:
            Iniciales del autor (ej: 'Juan Pérez' -> 'JP')
        """
        words = self.value.split()
        return "".join(w[0].upper() for w in words if w)

    def get_display_name(self, max_length: int = 50) -> str:
        """Obtiene nombre para display con truncamiento inteligente.

        Args:
            max_length: Longitud máxima

        Returns:
            Nombre truncado si es necesario
        """
        if len(self.value) <= max_length:
            return self.value
        return self.value[: max_length - 3] + "..."

    def matches(self, other: str) -> bool:
        """Verifica si coincide con otro nombre (case-insensitive)."""
        return self.value.lower() == other.lower()

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)
