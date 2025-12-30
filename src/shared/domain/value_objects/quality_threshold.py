"""Value Object: QualityThreshold para umbral mínimo de calidad de contenido."""

from dataclasses import dataclass
from typing import Optional

from src.shared.domain.value_objects.score import Score


@dataclass(frozen=True)
class QualityThreshold(Score):
    """
    Value Object inmutable para umbral de calidad de contenido.

    Hereda de Score para reutilizar validación y operaciones matemáticas.
    Agrega métodos específicos de filtrado y evaluación de umbrales.

    Define el score mínimo de calidad (0.0-1.0) que debe tener el contenido
    para ser aceptado durante el proceso de fetch.
    """

    @classmethod
    def minimum(cls, description: Optional[str] = None) -> "QualityThreshold":
        """Umbral mínimo (0.0) - acepta todo contenido."""
        return cls(
            value=0.0,
            description=description or "Umbral mínimo - acepta todo contenido",
        )

    @classmethod
    def low(cls, description: Optional[str] = None) -> "QualityThreshold":
        """Umbral bajo (0.3) - filtrado básico."""
        return cls(
            value=0.3,
            description=description or "Umbral bajo - filtrado básico",
        )

    @classmethod
    def medium(cls, description: Optional[str] = None) -> "QualityThreshold":
        """Umbral medio (0.5) - filtrado moderado."""
        return cls(
            value=0.5,
            description=description or "Umbral medio - filtrado moderado",
        )

    @classmethod
    def high(cls, description: Optional[str] = None) -> "QualityThreshold":
        """Umbral alto (0.7) - filtrado estricto."""
        return cls(
            value=0.7,
            description=description or "Umbral alto - filtrado estricto",
        )

    @classmethod
    def maximum(cls, description: Optional[str] = None) -> "QualityThreshold":
        """Umbral máximo (0.9) - solo contenido premium."""
        return cls(
            value=0.9,
            description=description or "Umbral máximo - solo contenido premium",
        )

    @classmethod
    def create(
        cls, score: float, description: Optional[str] = None
    ) -> "QualityThreshold":
        """Factory method para crear umbral con score específico."""
        return cls(value=score, description=description)

    # Sobrescribir meets_threshold de Score para validar el content_score
    def meets_threshold(self, content_score: float) -> bool:
        """
        Verifica si un score de contenido cumple el umbral.

        Sobrescribe el método de Score para agregar validación del content_score.
        """
        if not isinstance(content_score, (int, float)):
            raise ValueError("Content score must be a number")
        return content_score >= self.value

    def passes_filter(self, content_scores: list[float]) -> list[bool]:
        """Filtra una lista de scores basado en el umbral."""
        return [self.meets_threshold(score) for score in content_scores]

    def get_accepted_count(self, content_scores: list[float]) -> int:
        """Cuenta cuántos contenidos pasarían el umbral."""
        return sum(self.passes_filter(content_scores))

    def get_rejection_rate(self, content_scores: list[float]) -> float:
        """Calcula la tasa de rechazo (0.0-1.0) para una lista de scores."""
        if not content_scores:
            return 0.0
        accepted = self.get_accepted_count(content_scores)
        return 1.0 - (accepted / len(content_scores))

    @property
    def strictness_level(self) -> str:
        """
        Nivel de exigencia del umbral.

        Mapea el level de Score a terminología de strictness.
        """
        mapping = {
            "very_low": "very_permissive",
            "low": "permissive",
            "medium": "balanced",
            "high": "strict",
            "very_high": "very_strict",
        }
        return mapping.get(self.level, "balanced")

    @property
    def is_permissive(self) -> bool:
        """Indica si es un umbral permisivo (<= 0.4)."""
        return self.value <= 0.4

    @property
    def is_strict(self) -> bool:
        """Indica si es un umbral estricto (>= 0.7)."""
        return self.value >= 0.7

    # Backward compatibility: exponer 'score' como alias de 'value'
    @property
    def score(self) -> float:
        """Alias de value para backward compatibility."""
        return self.value

    def get_recommendation(self) -> str:
        """Recomendación basada en el nivel de umbral."""
        level = self.strictness_level
        recommendations = {
            "very_permissive": "Considera elevar el umbral para mejorar calidad",
            "permissive": "Umbral permisivo, bueno para exploración",
            "balanced": "Umbral equilibrado entre calidad y cantidad",
            "strict": "Umbral estricto, garantiza alta calidad",
            "very_strict": "Umbral muy estricto, puede filtrar contenido válido",
        }
        return recommendations.get(level, "Umbral de calidad configurado")

    def __str__(self) -> str:
        """Representación string con semántica de umbral."""
        if self.description:
            return f"Threshold: {self.percentage_str} ({self.description})"
        return f"Threshold: {self.percentage_str}"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"QualityThreshold(value={self.value:.2f}, description='{self.description}')"
