"""Interface para DetectArticleLanguageHandler."""

from typing import Protocol

from .command import DetectArticleLanguageCommand
from .result import LanguageDetectionResult


class IDetectArticleLanguageHandler(Protocol):
    """
    Interface para handler de detección de idioma.

    Dependency Inversion: Application layer depende de esta interface.
    """

    async def handle(
        self, command: DetectArticleLanguageCommand
    ) -> LanguageDetectionResult:
        """
        Detecta idioma del artículo.

        Args:
            command: Comando con article_id y configuración

        Returns:
            LanguageDetectionResult con idioma detectado y confianza
        """
        ...
