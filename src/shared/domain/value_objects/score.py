"""Value Object base para scores normalizados (0.0-1.0)."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Score:
    """
    Value Object base para scores normalizados entre 0.0 y 1.0.

    Proporciona validación, comparación y operaciones comunes para scores.
    Puede ser usado directamente o heredado por VOs específicos de dominio.

    Características:
    - Inmutable (frozen=True)
    - Validación automática en construcción
    - Operaciones de comparación
    - Conversión a porcentaje
    - Operaciones matemáticas seguras (ajuste, combinación)

    Example:
        >>> score = Score(0.75)
        >>> score.value
        0.75
        >>> score.percentage
        75.0
        >>> score.is_high()
        True

        >>> adjusted = score.adjust_by(0.1)
        >>> adjusted.value
        0.85
    """

    value: float
    description: Optional[str] = None

    # Constantes de rango
    MIN_VALUE: float = 0.0
    MAX_VALUE: float = 1.0

    # Umbrales por defecto (pueden ser sobrescritos en subclases)
    HIGH_THRESHOLD: float = 0.7
    MEDIUM_THRESHOLD: float = 0.4
    LOW_THRESHOLD: float = 0.2

    def __post_init__(self):
        """Validación en construcción."""
        if not isinstance(self.value, (int, float)):
            raise TypeError(
                f"Score value must be numeric, got {type(self.value).__name__}"
            )

        if not (self.MIN_VALUE <= self.value <= self.MAX_VALUE):
            raise ValueError(
                f"Score must be between {self.MIN_VALUE} and {self.MAX_VALUE}, "
                f"got {self.value}"
            )

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def create(cls, value: float, description: Optional[str] = None) -> "Score":
        """
        Factory method para crear Score.

        Args:
            value: Valor del score (0.0-1.0)
            description: Descripción opcional del score

        Returns:
            Nueva instancia de Score
        """
        return cls(value=value, description=description)

    @classmethod
    def zero(cls, description: Optional[str] = None) -> "Score":
        """Score mínimo (0.0)."""
        return cls(value=0.0, description=description or "Mínimo")

    @classmethod
    def maximum(cls, description: Optional[str] = None) -> "Score":
        """Score máximo (1.0)."""
        return cls(value=1.0, description=description or "Máximo")

    @classmethod
    def half(cls, description: Optional[str] = None) -> "Score":
        """Score medio (0.5)."""
        return cls(value=0.5, description=description or "Medio")

    @classmethod
    def low(cls, description: Optional[str] = None) -> "Score":
        """Score bajo (0.3)."""
        return cls(value=0.3, description=description or "Bajo")

    @classmethod
    def high(cls, description: Optional[str] = None) -> "Score":
        """Score alto (0.8)."""
        return cls(value=0.8, description=description or "Alto")

    # =========================================================================
    # Propiedades de Clasificación
    # =========================================================================

    def is_high(self) -> bool:
        """Verifica si es un score alto (>= HIGH_THRESHOLD)."""
        return self.value >= self.HIGH_THRESHOLD

    def is_medium(self) -> bool:
        """Verifica si es un score medio (MEDIUM_THRESHOLD <= x < HIGH_THRESHOLD)."""
        return self.MEDIUM_THRESHOLD <= self.value < self.HIGH_THRESHOLD

    def is_low(self) -> bool:
        """Verifica si es un score bajo (< MEDIUM_THRESHOLD)."""
        return self.value < self.MEDIUM_THRESHOLD

    def is_very_high(self) -> bool:
        """Verifica si es muy alto (>= 0.9)."""
        return self.value >= 0.9

    def is_very_low(self) -> bool:
        """Verifica si es muy bajo (<= 0.1)."""
        return self.value <= 0.1

    def is_zero(self) -> bool:
        """Verifica si es exactamente cero."""
        return self.value == 0.0

    def is_maximum(self) -> bool:
        """Verifica si es exactamente el máximo."""
        return self.value == 1.0

    @property
    def level(self) -> str:
        """
        Nivel del score como string.

        Returns:
            'very_high', 'high', 'medium', 'low', o 'very_low'
        """
        if self.is_very_high():
            return "very_high"
        elif self.is_high():
            return "high"
        elif self.is_medium():
            return "medium"
        elif self.is_very_low():
            return "very_low"
        else:
            return "low"

    # =========================================================================
    # Conversiones y Representaciones
    # =========================================================================

    @property
    def percentage(self) -> float:
        """Score como porcentaje (0-100)."""
        return self.value * 100

    @property
    def percentage_str(self) -> str:
        """Score como string de porcentaje formateado."""
        return f"{self.percentage:.1f}%"

    def to_float(self) -> float:
        """Conversión explícita a float."""
        return self.value

    def __float__(self) -> float:
        """Conversión implícita a float."""
        return self.value

    # =========================================================================
    # Operaciones Matemáticas
    # =========================================================================

    def adjust_by(self, amount: float) -> "Score":
        """
        Ajusta el score en una cantidad específica.

        El resultado se mantiene dentro del rango válido [0.0, 1.0].

        Args:
            amount: Cantidad a ajustar (puede ser negativo)

        Returns:
            Nueva instancia con score ajustado

        Example:
            >>> score = Score(0.5)
            >>> adjusted = score.adjust_by(0.2)
            >>> adjusted.value
            0.7
            >>> adjusted = score.adjust_by(-0.6)  # Se limita a 0.0
            >>> adjusted.value
            0.0
        """
        new_value = min(self.MAX_VALUE, max(self.MIN_VALUE, self.value + amount))
        return self.__class__(value=new_value, description=self.description)

    def multiply_by(self, factor: float) -> "Score":
        """
        Multiplica el score por un factor.

        El resultado se mantiene dentro del rango válido [0.0, 1.0].

        Args:
            factor: Factor multiplicador (debe ser >= 0)

        Returns:
            Nueva instancia con score multiplicado

        Raises:
            ValueError: Si el factor es negativo

        Example:
            >>> score = Score(0.5)
            >>> multiplied = score.multiply_by(1.5)
            >>> multiplied.value
            0.75
        """
        if factor < 0:
            raise ValueError("Factor must be non-negative")

        new_value = min(self.MAX_VALUE, self.value * factor)
        return self.__class__(value=new_value, description=self.description)

    def combine_with(self, other: "Score", weight: float = 0.5) -> "Score":
        """
        Combina con otro score usando promedio ponderado.

        Args:
            other: Otro Score
            weight: Peso del otro score (0.0-1.0), default 0.5 (promedio simple)

        Returns:
            Nuevo Score con valor combinado

        Raises:
            ValueError: Si weight no está en [0.0, 1.0]

        Example:
            >>> score1 = Score(0.6)
            >>> score2 = Score(0.8)
            >>> combined = score1.combine_with(score2)  # Promedio simple
            >>> combined.value
            0.7
            >>> combined = score1.combine_with(score2, weight=0.75)  # Más peso a score2
            >>> combined.value
            0.75
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")

        combined_value = (self.value * (1 - weight)) + (other.value * weight)
        return self.__class__(value=combined_value, description=self.description)

    def average_with(self, *others: "Score") -> "Score":
        """
        Calcula el promedio con otros scores.

        Args:
            *others: Otros scores para promediar

        Returns:
            Nuevo Score con el promedio

        Example:
            >>> score1 = Score(0.5)
            >>> score2 = Score(0.7)
            >>> score3 = Score(0.9)
            >>> avg = score1.average_with(score2, score3)
            >>> avg.value
            0.7
        """
        all_values = [self.value] + [s.value for s in others]
        avg_value = sum(all_values) / len(all_values)
        return self.__class__(value=avg_value, description=self.description)

    def invert(self) -> "Score":
        """
        Invierte el score (1.0 - value).

        Returns:
            Nuevo Score con valor invertido

        Example:
            >>> score = Score(0.3)
            >>> inverted = score.invert()
            >>> inverted.value
            0.7
        """
        return self.__class__(value=1.0 - self.value, description=self.description)

    # =========================================================================
    # Comparaciones
    # =========================================================================

    def meets_threshold(self, threshold: float) -> bool:
        """
        Verifica si cumple un umbral mínimo.

        Args:
            threshold: Umbral mínimo (0.0-1.0)

        Returns:
            True si el score >= threshold
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return self.value >= threshold

    def __lt__(self, other: "Score") -> bool:
        """Comparación menor que."""
        if not isinstance(other, Score):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: "Score") -> bool:
        """Comparación menor o igual."""
        if not isinstance(other, Score):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: "Score") -> bool:
        """Comparación mayor que."""
        if not isinstance(other, Score):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: "Score") -> bool:
        """Comparación mayor o igual."""
        if not isinstance(other, Score):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: object) -> bool:
        """Comparación de igualdad."""
        if not isinstance(other, Score):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash para usar en sets y dicts."""
        return hash((self.value, self.description))

    # =========================================================================
    # Representaciones String
    # =========================================================================

    def __str__(self) -> str:
        """Representación string legible."""
        if self.description:
            return f"{self.description}: {self.percentage_str}"
        return self.percentage_str

    def __repr__(self) -> str:
        """Representación para debugging."""
        if self.description:
            return f"Score(value={self.value:.2f}, description='{self.description}')"
        return f"Score(value={self.value:.2f})"
