"""Interface para GenerateArticleSummary handler."""

from typing import Protocol

from .command import GenerateArticleSummaryCommand
from .result import GenerateArticleSummaryResult


class IGenerateArticleSummaryHandler(Protocol):
    """Interface para handler de generación de summary."""

    async def handle(
        self, command: GenerateArticleSummaryCommand
    ) -> GenerateArticleSummaryResult:
        """
        Genera summary de artículo.

        Args:
            command: Comando con configuración

        Returns:
            Result con summary generado

        Raises:
            ArticleNotFoundError: Si artículo no existe
            ArticleHasNoContentError: Si artículo sin contenido
            SummaryGenerationError: Si falla la generación
        """
        ...
