"""Interface para UpdateSource command handler - CQRS."""

from abc import ABC, abstractmethod

from .command import UpdateSourceCommand
from .result import UpdateSourceResult


class IUpdateRssFeedHandler(ABC):
    """Interface CQRS para handler de actualización de fuentes RSS usando Source aggregate."""

    @abstractmethod
    async def handle(self, command: UpdateSourceCommand) -> UpdateSourceResult:
        """
        Maneja el comando de actualización de fuente RSS.

        Args:
            command: Comando con información de actualización de la fuente

        Returns:
            UpdateSourceResult: Resultado de la operación

        Raises:
            SourceNotFoundError: Si la fuente no existe
            InvalidSourceUpdateError: Si los datos de actualización son inválidos
            SourceConfigurationError: Si la configuración es incorrecta
        """
        pass
