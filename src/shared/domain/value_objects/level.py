"""Generic Level Value Object - 5 niveles de calidad/prioridad."""

from enum import Enum

from src.shared.kernel.value_object import IValueObject


class LevelEnum(Enum):
    """Niveles genéricos de calidad/prioridad (5 niveles)."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Level(IValueObject):
    """
    Value Object genérico para niveles de calidad/prioridad.

    Encapsula la lógica de evaluación de niveles y comparaciones.
    Usa 5 niveles: VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH.
    """

    def __init__(self, level: LevelEnum):
        """
        Inicializa Level.

        Args:
            level: Nivel

        Raises:
            ValueError: Si el nivel no es válido
        """
        if not isinstance(level, LevelEnum):
            raise ValueError("level debe ser LevelEnum")

        self._level: LevelEnum = level

    @property
    def value(self) -> str:
        """Valor string del nivel."""
        return self._level.value

    @property
    def enum_value(self) -> LevelEnum:
        """Valor enum del nivel."""
        return self._level

    @property
    def numeric_value(self) -> int:
        """Valor numérico para comparaciones (0-4)."""
        level_mapping = {
            LevelEnum.VERY_LOW: 0,
            LevelEnum.LOW: 1,
            LevelEnum.MEDIUM: 2,
            LevelEnum.HIGH: 3,
            LevelEnum.VERY_HIGH: 4,
        }
        return level_mapping[self._level]

    @property
    def score(self) -> float:
        """Score normalizado 0.0-1.0."""
        score_mapping = {
            LevelEnum.VERY_LOW: 0.1,
            LevelEnum.LOW: 0.3,
            LevelEnum.MEDIUM: 0.5,
            LevelEnum.HIGH: 0.75,
            LevelEnum.VERY_HIGH: 0.95,
        }
        return score_mapping[self._level]

    @staticmethod
    def very_low() -> "Level":
        """Crea nivel VERY_LOW."""
        return Level(LevelEnum.VERY_LOW)

    @staticmethod
    def low() -> "Level":
        """Crea nivel LOW."""
        return Level(LevelEnum.LOW)

    @staticmethod
    def medium() -> "Level":
        """Crea nivel MEDIUM."""
        return Level(LevelEnum.MEDIUM)

    @staticmethod
    def high() -> "Level":
        """Crea nivel HIGH."""
        return Level(LevelEnum.HIGH)

    @staticmethod
    def very_high() -> "Level":
        """Crea nivel VERY_HIGH."""
        return Level(LevelEnum.VERY_HIGH)

    @staticmethod
    def from_string(level_str: str) -> "Level":
        """
        Crea Level desde string.

        Args:
            level_str: Nivel como string

        Returns:
            Level correspondiente

        Raises:
            ValueError: Si el string no corresponde a un nivel válido
        """
        if not level_str or not isinstance(level_str, str):
            raise ValueError("level_str debe ser string no vacío")

        try:
            level_enum = LevelEnum(level_str.lower())
            return Level(level_enum)
        except ValueError:
            valid_levels = [l.value for l in LevelEnum]
            raise ValueError(f"Nivel inválido: {level_str}. Válidos: {valid_levels}")

    @staticmethod
    def from_score(score: float) -> "Level":
        """
        Crea Level basado en score numérico (0.0-1.0).

        Args:
            score: Puntuación entre 0.0 y 1.0

        Returns:
            Level correspondiente

        Raises:
            ValueError: Si el score está fuera del rango válido
        """
        if not isinstance(score, (int, float)):
            raise ValueError("score debe ser numérico")

        if score < 0.0 or score > 1.0:
            raise ValueError("score debe estar entre 0.0 y 1.0")

        if score < 0.2:
            return Level.very_low()
        elif score < 0.4:
            return Level.low()
        elif score < 0.65:
            return Level.medium()
        elif score < 0.85:
            return Level.high()
        else:
            return Level.very_high()

    def is_very_low(self) -> bool:
        """True si es nivel muy bajo."""
        return self._level == LevelEnum.VERY_LOW

    def is_low(self) -> bool:
        """True si es nivel bajo."""
        return self._level == LevelEnum.LOW

    def is_medium(self) -> bool:
        """True si es nivel medio."""
        return self._level == LevelEnum.MEDIUM

    def is_high(self) -> bool:
        """True si es nivel alto."""
        return self._level == LevelEnum.HIGH

    def is_very_high(self) -> bool:
        """True si es nivel muy alto."""
        return self._level == LevelEnum.VERY_HIGH

    def is_acceptable(self) -> bool:
        """True si el nivel es aceptable (MEDIUM o superior)."""
        return self._level in [
            LevelEnum.MEDIUM,
            LevelEnum.HIGH,
            LevelEnum.VERY_HIGH,
        ]

    def meets_minimum_threshold(self, threshold: "Level") -> bool:
        """
        True si el nivel cumple el umbral mínimo.

        Args:
            threshold: Nivel mínimo requerido

        Returns:
            True si cumple o supera el umbral
        """
        return self.numeric_value >= threshold.numeric_value

    def __str__(self) -> str:
        return self._level.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Level):
            return False
        return self._level == other._level

    def __lt__(self, other: "Level") -> bool:
        if not isinstance(other, Level):
            return NotImplemented
        return self.numeric_value < other.numeric_value

    def __le__(self, other: "Level") -> bool:
        if not isinstance(other, Level):
            return NotImplemented
        return self.numeric_value <= other.numeric_value

    def __gt__(self, other: "Level") -> bool:
        if not isinstance(other, Level):
            return NotImplemented
        return self.numeric_value > other.numeric_value

    def __ge__(self, other: "Level") -> bool:
        if not isinstance(other, Level):
            return NotImplemented
        return self.numeric_value >= other.numeric_value

    def __hash__(self) -> int:
        return hash(self._level)
