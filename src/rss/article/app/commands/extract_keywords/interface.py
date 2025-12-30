"""Interface para ExtractArticleKeywords command handler."""

from typing import Protocol

from .command import ExtractArticleKeywordsCommand
from .result import KeywordExtractionResult


class IExtractArticleKeywordsHandler(Protocol):
    """
    Interface para handler de extracción de keywords.

    Sigue Dependency Inversion Principle - permite inyectar handler
    sin depender de implementación concreta.
    """

    async def handle(
        self, command: ExtractArticleKeywordsCommand
    ) -> KeywordExtractionResult:
        """
        Extrae keywords de un artículo.

        Args:
            command: Comando con configuración de extracción

        Returns:
            KeywordExtractionResult con keywords extraídas o error
        """
        ...
