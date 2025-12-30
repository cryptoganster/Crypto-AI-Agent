"""Interface para CalculateArticleQuality handler."""

from abc import ABC, abstractmethod

from .command import CalculateArticleQualityCommand
from .result import CalculateArticleQualityResult


class ICalculateArticleQualityHandler(ABC):
    """Interface para handler de cálculo de quality completo."""

    @abstractmethod
    async def handle(
        self, command: CalculateArticleQualityCommand
    ) -> CalculateArticleQualityResult:
        """
        Calcula quality (score + level) de un artículo.

        Args:
            command: Comando con article_id

        Returns:
            CalculateArticleQualityResult con score y level calculados
        """
        pass
