"""
Value Object para títulos de artículos RSS.
Encapsula validación y normalización de títulos.
"""

import re
from dataclasses import dataclass

from src.shared.kernel.value_object import IValueObject


@dataclass(frozen=True)
class ArticleTitle(IValueObject):
    """Value Object para títulos de artículos RSS."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.value:
            raise ValueError("Título del artículo no puede estar vacío")

        if len(self.value.strip()) == 0:
            raise ValueError("Título del artículo no puede ser solo espacios")

        if len(self.value) > 500:
            raise ValueError("Título del artículo no puede exceder 500 caracteres")

        # Normalizar título (eliminar espacios extra, etc.)
        normalized = re.sub(r"\s+", " ", self.value.strip())
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, title: str) -> "ArticleTitle":
        """Factory method para crear título con valores por defecto."""
        if not title or not title.strip():
            return cls("Untitled Article")
        return cls(title)

    def is_clickbait(self) -> bool:
        """Detecta si el título parece clickbait."""
        clickbait_patterns = [
            r"\d+\s+(reasons|ways|things|secrets)",
            r"you won't believe",
            r"shocking",
            r"one weird trick",
        ]

        lower_title = self.value.lower()
        return any(re.search(pattern, lower_title) for pattern in clickbait_patterns)

    def truncate(self, max_length: int = 100, suffix: str = "...") -> str:
        """Trunca el título a una longitud máxima con sufijo.

        Args:
            max_length: Longitud máxima del título
            suffix: Sufijo a agregar si se trunca

        Returns:
            Título truncado con sufijo si excede max_length
        """
        if len(self.value) <= max_length:
            return self.value

        return self.value[:max_length] + suffix

    def get_word_count(self) -> int:
        """Obtiene conteo de palabras."""
        return len(self.value.split())

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)
