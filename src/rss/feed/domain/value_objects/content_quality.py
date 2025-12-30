"""Value Object: ContentQuality para niveles de calidad del contenido."""

from enum import Enum
from typing import List


class ContentQuality(Enum):
    """Niveles de calidad del contenido."""

    UNKNOWN = "unknown"  # Sin analizar
    LOW = "low"  # Calidad baja
    MEDIUM = "medium"  # Calidad media
    HIGH = "high"  # Calidad alta
    PREMIUM = "premium"  # Calidad premium

    @classmethod
    def from_score(cls, score: float) -> "ContentQuality":
        """Convierte un score numérico (0.0-1.0) a ContentQuality."""
        if not isinstance(score, (int, float)):
            return cls.UNKNOWN

        if score < 0:
            return cls.UNKNOWN
        elif score < 0.3:
            return cls.LOW
        elif score < 0.6:
            return cls.MEDIUM
        elif score < 0.8:
            return cls.HIGH
        else:
            return cls.PREMIUM

    @classmethod
    def get_publishable_qualities(cls) -> List["ContentQuality"]:
        """Retorna calidades aptas para publicación automática."""
        return [cls.HIGH, cls.PREMIUM]

    @classmethod
    def get_manual_review_qualities(cls) -> List["ContentQuality"]:
        """Retorna calidades que requieren revisión manual."""
        return [cls.UNKNOWN, cls.LOW]

    @property
    def numeric_score(self) -> float:
        """Convierte la calidad a score numérico."""
        score_mapping = {
            self.UNKNOWN: 0.0,
            self.LOW: 0.2,
            self.MEDIUM: 0.5,
            self.HIGH: 0.7,
            self.PREMIUM: 0.9,
        }
        return score_mapping[self]

    @property
    def is_auto_publishable(self) -> bool:
        """Indica si es apta para publicación automática."""
        return self in self.get_publishable_qualities()

    @property
    def requires_human_review(self) -> bool:
        """Indica si requiere revisión humana."""
        return self in self.get_manual_review_qualities()

    @property
    def priority_score(self) -> int:
        """Score de prioridad para ordenamiento."""
        priority_mapping = {
            self.PREMIUM: 5,
            self.HIGH: 4,
            self.MEDIUM: 3,
            self.LOW: 2,
            self.UNKNOWN: 1,
        }
        return priority_mapping[self]

    def can_upgrade_to(self, target_quality: "ContentQuality") -> bool:
        """Valida si se puede actualizar a una calidad superior."""
        return target_quality.priority_score > self.priority_score

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other) -> bool:
        """Permite comparación ordenada por prioridad."""
        if not isinstance(other, ContentQuality):
            return NotImplemented
        return self.priority_score < other.priority_score
