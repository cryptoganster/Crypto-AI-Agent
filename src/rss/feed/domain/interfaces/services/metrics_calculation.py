"""Interface para Source Metrics Calculation Service."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.rss.feed.domain.value_objects import MetricsThreshold, PerformanceTrend
from src.rss.feed.domain.value_objects.metrics import FetchData, SourceMetrics
from src.scraping.domain.entities import ScrapingRecord


class ISourceMetricsCalculationService(ABC):
    """
    Interface para Domain Service de cálculo de métricas para el agregado Source.

    Responsabilidades:
    - Calcular métricas agregadas del historial de scraping
    - Detectar cambios significativos en métricas
    - Analizar tendencias de rendimiento
    - Proporcionar lógica especializada de análisis (SIN emitir eventos)
    """

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...
