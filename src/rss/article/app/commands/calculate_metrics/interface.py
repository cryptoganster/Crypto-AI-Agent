"""Interface para CalculateArticleMetrics handler."""

from typing import Protocol

from .command import CalculateArticleMetricsCommand
from .result import CalculateArticleMetricsResult


class ICalculateArticleMetricsHandler(Protocol):
    """
    Interface para handler de cálculo de métricas.

    Dependency Inversion Principle: Dependencias dependen de abstracción.
    """

    async def handle(
        self, command: CalculateArticleMetricsCommand
    ) -> CalculateArticleMetricsResult:
        """
        Calcula métricas de artículo.

        Args:
            command: Comando con configuración

        Returns:
            Result con métricas calculadas

        Raises:
            ArticleNotFoundError: Si artículo no existe
            MetricsCalculationError: Si falla el cálculo
        """
        ...
