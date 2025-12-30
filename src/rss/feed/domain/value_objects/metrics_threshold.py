"""MetricsThreshold Value Object - Define umbrales para análisis de métricas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsThreshold:
    """
    Value Object que define umbrales para análisis de métricas de Source.

    Encapsula configuraciones de umbrales para evitar magic numbers
    en la lógica de negocio de análisis de métricas.
    """

    success_rate_change_threshold: float = 0.05  # 5% cambio significativo
    performance_analysis_sample_size: int = 20  # Registros para análisis de tendencia
    minimum_samples_for_analysis: int = 5  # Mínimo para análisis confiable
    high_confidence_threshold: float = 0.7  # Umbral para alta confidence
    decline_attention_threshold: float = 0.1  # Umbral de declive que requiere atención
    trend_comparison_threshold: float = (
        0.1  # Diferencia para considerar improving/declining
    )

    def __post_init__(self):
        """Validaciones post-inicialización."""
        if not 0.0 < self.success_rate_change_threshold <= 1.0:
            raise ValueError("Success rate change threshold debe estar entre 0.0 y 1.0")

        if self.performance_analysis_sample_size <= 0:
            raise ValueError("Performance analysis sample size debe ser positivo")

        if self.minimum_samples_for_analysis <= 0:
            raise ValueError("Minimum samples for analysis debe ser positivo")

        if not 0.0 <= self.high_confidence_threshold <= 1.0:
            raise ValueError("High confidence threshold debe estar entre 0.0 y 1.0")

        if not 0.0 < self.decline_attention_threshold <= 1.0:
            raise ValueError("Decline attention threshold debe estar entre 0.0 y 1.0")

        if not 0.0 < self.trend_comparison_threshold <= 1.0:
            raise ValueError("Trend comparison threshold debe estar entre 0.0 y 1.0")

    @classmethod
    def default(cls) -> "MetricsThreshold":
        """Crea instancia con valores por defecto."""
        return cls()

    @classmethod
    def conservative(cls) -> "MetricsThreshold":
        """Crea instancia con umbrales conservadores (más restrictivos)."""
        return cls(
            success_rate_change_threshold=0.03,  # 3% más sensible
            performance_analysis_sample_size=30,  # Más datos requeridos
            minimum_samples_for_analysis=10,  # Más muestras mínimas
            high_confidence_threshold=0.8,  # Mayor confidence requerida
            decline_attention_threshold=0.05,  # Más sensible a declives
            trend_comparison_threshold=0.05,  # Más sensible a cambios
        )

    @classmethod
    def relaxed(cls) -> "MetricsThreshold":
        """Crea instancia con umbrales relajados (menos restrictivos)."""
        return cls(
            success_rate_change_threshold=0.1,  # 10% menos sensible
            performance_analysis_sample_size=10,  # Menos datos requeridos
            minimum_samples_for_analysis=3,  # Menos muestras mínimas
            high_confidence_threshold=0.5,  # Menor confidence requerida
            decline_attention_threshold=0.2,  # Menos sensible a declives
            trend_comparison_threshold=0.15,  # Menos sensible a cambios
        )

    def is_significant_change(self, change: float) -> bool:
        """True si el cambio es significativo según el umbral."""
        return abs(change) >= self.success_rate_change_threshold

    def has_sufficient_samples(self, sample_count: int) -> bool:
        """True si hay suficientes muestras para análisis confiable."""
        return sample_count >= self.minimum_samples_for_analysis

    def get_analysis_confidence(self, sample_count: int) -> float:
        """
        Calcula confidence basado en el tamaño de muestra.

        Args:
            sample_count: Número de muestras disponibles

        Returns:
            Confidence entre 0.0 y 1.0
        """
        if sample_count < self.minimum_samples_for_analysis:
            return 0.0

        # Confidence aumenta linealmente hasta el sample size óptimo
        return min(sample_count / self.performance_analysis_sample_size, 1.0)
