"""Value Object para categoría de artículo."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ArticleCategory:
    """
    Categoría de un artículo.

    Value Object inmutable que representa la categoría temática
    de un artículo (ej: "Technology", "Business", "Sports").

    Attributes:
        name: Nombre de la categoría
        confidence: Nivel de confianza de la categorización (0.0-1.0)
    """

    name: str
    confidence: float = 1.0

    def __post_init__(self):
        """Valida los valores del Value Object."""
        if not self.name or not self.name.strip():
            raise ValueError("name no puede estar vacío")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence debe estar entre 0.0 y 1.0, recibido: {self.confidence}"
            )

        # Normalizar name (strip y capitalize)
        object.__setattr__(self, "name", self.name.strip().capitalize())

    @classmethod
    def create(cls, name: str, confidence: float = 1.0) -> "ArticleCategory":
        """
        Factory method para crear ArticleCategory.

        Args:
            name: Nombre de la categoría
            confidence: Nivel de confianza (default: 1.0)

        Returns:
            Nueva instancia de ArticleCategory

        Raises:
            ValueError: Si name está vacío o confidence fuera de rango
        """
        return cls(name=name, confidence=confidence)

    def is_high_confidence(self) -> bool:
        """
        Verifica si la categorización tiene alta confianza.

        Returns:
            True si confidence > 0.7
        """
        return self.confidence > 0.7

    def is_low_confidence(self) -> bool:
        """
        Verifica si la categorización tiene baja confianza.

        Returns:
            True si confidence < 0.3
        """
        return self.confidence < 0.3

    def __str__(self) -> str:
        """Representación en string."""
        if self.confidence < 1.0:
            return f"{self.name} ({self.confidence:.1%})"
        return self.name

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ArticleCategory(name='{self.name}', confidence={self.confidence:.2f})"
