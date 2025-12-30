"""Interface para handler de conversión HTML a Markdown."""

from typing import Protocol

from .command import ConvertArticleToMarkdownCommand
from .result import ConvertArticleToMarkdownResult


class IConvertArticleToMarkdownHandler(Protocol):
    """
    Interface para handler de conversión HTML a Markdown.

    Dependency Inversion Principle - permite inyectar implementación concreta.
    """

    async def handle(
        self, command: ConvertArticleToMarkdownCommand
    ) -> ConvertArticleToMarkdownResult:
        """
        Convierte contenido HTML procesado a Markdown.

        Args:
            command: Comando con article_id

        Returns:
            ConvertArticleToMarkdownResult con resultado de la operación
        """
        ...
