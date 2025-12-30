"""SourceMetricsCalculationService - Domain Service para cálculo de métricas de Source."""

from typing import TYPE_CHECKING, List, Optional

from src.rss.feed.domain.interfaces.services.metrics_calculation import (
    ISourceMetricsCalculationService,
)
from src.rss.feed.domain.value_objects import MetricsThreshold
from src.rss.feed.domain.value_objects.metrics import FetchData, SourceMetrics
from src.rss.feed.domain.value_objects.performance_trend import (
    PerformanceTrend,
    TrendDirection,
)
from src.scraping.domain.entities import ScrapingRecord

if TYPE_CHECKING:
    from src.rss.feed.domain.aggregates import Source


class SourceMetricsCalculationService(ISourceMetricsCalculationService):
    """
    Domain Service responsable del cálculo de métricas para el agregado Source.

    Responsabilidades:
    - Calcular métricas agregadas del historial de scraping
    - Detectar cambios significativos en métricas
    - Analizar tendencias de rendimiento
    - Proporcionar lógica especializada de análisis (SIN emitir eventos)

    Nota: Los eventos son responsabilidad del agregado, no del domain service.
    """

    def __init__(self, thresholds: Optional[MetricsThreshold] = None):
        """
        Inicializa el service con umbrales configurables.

        Args:
            thresholds: Umbrales para análisis (usa defaults si es None)
        """
        self._thresholds = thresholds or MetricsThreshold.default()

    def calculate_metrics(
        self, scraping_history: List[ScrapingRecord]
    ) -> SourceMetrics:
        """
        Calcula métricas agregadas basadas en el historial de scraping.

        Args:
            scraping_history: Lista de ScrapingRecord para calcular métricas

        Returns:
            SourceMetrics calculadas del historial

        Raises:
            ValueError: Si scraping_history es None
        """
        if scraping_history is None:
            raise ValueError("scraping_history no puede ser None")

        if not scraping_history:
            return SourceMetrics.empty()

        # Convertir ScrapingRecords a FetchData para el cálculo de métricas
        fetch_data_list = self.convert_scraping_records_to_data(scraping_history)

        # Delegar cálculo al Value Object SourceMetrics
        return SourceMetrics.calculate_from_history(fetch_data_list)

    def has_significant_metrics_change(
        self, previous: Optional[SourceMetrics], current: SourceMetrics
    ) -> bool:
        """
        Determina si hubo un cambio significativo en las métricas.

        Args:
            previous: Métricas previas (puede ser None)
            current: Métricas actuales

        Returns:
            True si hay cambios significativos

        Raises:
            ValueError: Si current es None
        """
        if current is None:
            raise ValueError("current metrics no puede ser None")

        if previous is None:
            return True  # Primeras métricas siempre son significativas

        # Usar umbrales configurables en lugar de magic numbers
        success_rate_change = abs(previous.success_rate - current.success_rate)

        significant_changes = [
            previous.total_fetches != current.total_fetches,
            previous.successful_fetches != current.successful_fetches,
            previous.failed_fetches != current.failed_fetches,
            self._thresholds.is_significant_change(success_rate_change),
            previous.total_articles_discovered != current.total_articles_discovered,
            previous.total_articles_new != current.total_articles_new,
        ]

        return any(significant_changes)

    def analyze_performance_trends(
        self, recent_history: List[ScrapingRecord], global_metrics: SourceMetrics
    ) -> PerformanceTrend:
        """
        Analiza tendencias de rendimiento basadas en el historial reciente.

        Args:
            recent_history: Historial reciente de scraping
            global_metrics: Métricas globales para comparación

        Returns:
            PerformanceTrend con análisis de tendencias

        Raises:
            ValueError: Si los argumentos son None
        """
        if recent_history is None:
            raise ValueError("recent_history no puede ser None")
        if global_metrics is None:
            raise ValueError("global_metrics no puede ser None")

        # Verificar si hay suficientes datos para análisis
        if not self._thresholds.has_sufficient_samples(len(recent_history)):
            return PerformanceTrend.insufficient_data()

        # Calcular success rate reciente
        recent_successes = sum(1 for record in recent_history if record.is_successful())
        recent_success_rate = recent_successes / len(recent_history)
        global_success_rate = global_metrics.success_rate

        # Determinar dirección de tendencia usando umbrales configurables
        performance_delta = recent_success_rate - global_success_rate

        if performance_delta > self._thresholds.trend_comparison_threshold:
            direction = TrendDirection.IMPROVING
        elif performance_delta < -self._thresholds.trend_comparison_threshold:
            direction = TrendDirection.DECLINING
        else:
            direction = TrendDirection.STABLE

        # Calcular confidence basado en tamaño de muestra
        confidence = self._thresholds.get_analysis_confidence(len(recent_history))

        return PerformanceTrend(
            direction=direction,
            confidence=confidence,
            recent_success_rate=recent_success_rate,
            global_success_rate=global_success_rate,
            sample_size=len(recent_history),
        )

    def convert_scraping_records_to_data(
        self, scraping_records: List[ScrapingRecord]
    ) -> List[FetchData]:
        """
        Convierte lista de ScrapingRecord a lista de FetchData para cálculos.

        Args:
            scraping_records: Lista de ScrapingRecord del historial

        Returns:
            Lista de FetchData para uso en cálculo de métricas

        Raises:
            ValueError: Si scraping_records es None
        """
        if scraping_records is None:
            raise ValueError("scraping_records no puede ser None")

        return [
            FetchData(
                is_successful=record.is_successful(),
                is_failed=record.status.is_failed(),
                articles_found=record.articles_found,
                articles_new=record.articles_new,
                response_time_ms=record.response_time_ms,
                started_at=record.started_at,
                completed_at=record.completed_at,
            )
            for record in scraping_records
        ]
