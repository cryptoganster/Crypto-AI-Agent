"""PerformanceTrend Value Object - Representa tendencia de rendimiento de una fuente."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TrendDirection(Enum):
    """Dirección de la tendencia de rendimiento."""

    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class PerformanceTrend:
    """
    Value Object que representa la tendencia de rendimiento de una fuente.

    Encapsula el análisis de tendencias con confidence level y métricas de soporte.
    """

    direction: TrendDirection
    confidence: float  # 0.0 - 1.0
    recent_success_rate: float
    global_success_rate: float
    sample_size: int
    analysis_period_days: Optional[int] = None

    def __post_init__(self):
        """Validaciones post-inicialización."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence debe estar entre 0.0 y 1.0")

        if not 0.0 <= self.recent_success_rate <= 1.0:
            raise ValueError("Recent success rate debe estar entre 0.0 y 1.0")

        if not 0.0 <= self.global_success_rate <= 1.0:
            raise ValueError("Global success rate debe estar entre 0.0 y 1.0")

        if self.sample_size < 0:
            raise ValueError("Sample size debe ser no negativo")

    @classmethod
    def insufficient_data(cls) -> "PerformanceTrend":
        """Crea instancia para casos con datos insuficientes."""
        return cls(
            direction=TrendDirection.INSUFFICIENT_DATA,
            confidence=0.0,
            recent_success_rate=0.0,
            global_success_rate=0.0,
            sample_size=0,
        )

    def is_improving(self) -> bool:
        """True si la tendencia es de mejora."""
        return self.direction == TrendDirection.IMPROVING

    def is_declining(self) -> bool:
        """True si la tendencia es de declive."""
        return self.direction == TrendDirection.DECLINING

    def is_stable(self) -> bool:
        """True si la tendencia es estable."""
        return self.direction == TrendDirection.STABLE

    def has_sufficient_data(self) -> bool:
        """True si hay suficientes datos para análisis confiable."""
        return self.direction != TrendDirection.INSUFFICIENT_DATA

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """True si el confidence está por encima del threshold."""
        return self.confidence >= threshold

    def get_trend_strength(self) -> str:
        """Obtiene la fuerza de la tendencia basada en confidence."""
        if not self.has_sufficient_data():
            return "no_data"

        if self.confidence >= 0.8:
            return "strong"
        elif self.confidence >= 0.6:
            return "moderate"
        elif self.confidence >= 0.4:
            return "weak"
        else:
            return "unreliable"

    def get_performance_delta(self) -> float:
        """Obtiene la diferencia entre performance reciente y global."""
        return self.recent_success_rate - self.global_success_rate

    def requires_attention(self, decline_threshold: float = 0.1) -> bool:
        """
        True si la tendencia requiere atención (declive significativo).

        Args:
            decline_threshold: Umbral de declive que requiere atención
        """
        return (
            self.is_declining()
            and abs(self.get_performance_delta()) >= decline_threshold
            and self.confidence >= 0.5
        )
