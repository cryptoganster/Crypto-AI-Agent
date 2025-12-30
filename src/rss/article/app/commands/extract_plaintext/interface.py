"""Interface para el handler de extracción de plaintext."""

from typing import Protocol

from .command import ExtractArticlePlaintextCommand
from .result import PlaintextExtractionResult


class IExtractArticlePlaintextHandler(Protocol):
    """Interface para el handler de extracción de texto plano."""

    async def handle(
        self, command: ExtractArticlePlaintextCommand
    ) -> PlaintextExtractionResult:
        """Ejecuta la extracción de texto plano."""
        ...
