"""Value Object para score de legibilidad de artículos."""

from dataclasses import dataclass

# Constantes para validación de scores
MIN_SCORE = 0.0
"""Score mínimo válido para legibilidad."""

MAX_SCORE = 1.0
"""Score máximo válido para legibilidad."""


@dataclass(frozen=True)
class ReadabilityScore:
    """
    Value Object que representa el score de legibilidad de un artículo.

    El score está normalizado entre 0.0 y 1.0, donde:
    - 1.0 = Muy fácil de leer
    - 0.7-0.9 = Fácil de leer
    - 0.4-0.6 = Moderadamente difícil
    - 0.0-0.3 = Difícil de leer

    Basado en métricas como Flesch Reading Ease.
    """

    value: float

    def __post_init__(self):
        """Valida que el score esté en el rango correcto."""
        if not isinstance(self.value, (int, float)):
            raise TypeError("Score debe ser un número")

        if not MIN_SCORE <= self.value <= MAX_SCORE:
            raise ValueError(
                f"Score de legibilidad debe estar entre {MIN_SCORE} y {MAX_SCORE}, "
                f"recibido: {self.value}"
            )

    def is_easy_to_read(self) -> bool:
        """
        Determina si el contenido es fácil de leer.

        Returns:
            True si el score es >= 0.7
        """
        return self.value >= 0.7

    def is_difficult(self) -> bool:
        """
        Determina si el contenido es difícil de leer.

        Returns:
            True si el score es < 0.3
        """
        return self.value < 0.3

    def is_moderate(self) -> bool:
        """
        Determina si el contenido tiene dificultad moderada.

        Returns:
            True si el score está entre 0.3 y 0.7
        """
        return 0.3 <= self.value < 0.7

    def get_readability_level(self) -> str:
        """
        Obtiene el nivel de legibilidad como string descriptivo.

        Returns:
            Nivel de legibilidad: "very_easy", "easy", "moderate", "difficult", "very_difficult"
        """
        if self.value >= 0.9:
            return "very_easy"
        elif self.value >= 0.7:
            return "easy"
        elif self.value >= 0.5:
            return "moderate"
        elif self.value >= 0.3:
            return "difficult"
        else:
            return "very_difficult"

    def __str__(self) -> str:
        """Representación en string del score."""
        return f"{self.value:.2f}"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ReadabilityScore(value={self.value}, level={self.get_readability_level()})"
