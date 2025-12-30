"""
Value Object para resumen de artículos RSS.
Encapsula validación y normalización de resúmenes.
"""
from __future__ import annotations


import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RssArticleSummary:
    """Value Object para resúmenes de artículos RSS."""

    value: str

    def __post_init__(self):
        """Validación post-inicialización."""
        if self.value is None:
            raise ValueError("Resumen no puede ser None (usar empty string si vacío)")

        # Permitir resumen vacío
        if len(self.value.strip()) == 0:
            object.__setattr__(self, "value", "")
        else:
            if len(self.value) > 1000:
                raise ValueError("Resumen no puede exceder 1000 caracteres")

            # Normalizar espacios
            normalized = re.sub(r"\s+", " ", self.value.strip())
            object.__setattr__(self, "value", normalized)

    @classmethod
    def create(cls, summary: Optional[str]) -> Optional["ArticleSummary"]:
        """Factory method para crear resumen (retorna None si vacío)."""
        if not summary or not summary.strip():
            return None
        return cls(summary)

    def truncate(self, max_length: int = 200, suffix: str = "...") -> str:
        """Trunca el resumen a una longitud máxima con sufijo.

        Args:
            max_length: Longitud máxima del resumen
            suffix: Sufijo a agregar si se trunca

        Returns:
            Resumen truncado con sufijo si excede max_length
        """
        if len(self.value) <= max_length:
            return self.value

        return self.value[:max_length] + suffix

    @classmethod
    def empty(cls) -> "ArticleSummary":
        """Crea resumen vacío."""
        return cls("")

    @classmethod
    def from_content(cls, content: str, max_words: int = 50) -> "ArticleSummary":
        """Genera resumen automático desde contenido."""
        if not content or not content.strip():
            return cls.empty()

        words = content.split()
        if len(words) <= max_words:
            return cls(content)

        summary = " ".join(words[:max_words]) + "..."
        return cls(summary)

    def is_empty(self) -> bool:
        """Verifica si el resumen está vacío."""
        return len(self.value.strip()) == 0

    def get_word_count(self) -> int:
        """Obtiene conteo de palabras."""
        if self.is_empty():
            return 0
        return len(self.value.split())

    def is_within_limit(self, max_words: int = 50) -> bool:
        """Verifica si está dentro del límite de palabras."""
        return self.get_word_count() <= max_words

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __bool__(self) -> bool:
        """Permite usar en contextos booleanos."""
        return not self.is_empty()
