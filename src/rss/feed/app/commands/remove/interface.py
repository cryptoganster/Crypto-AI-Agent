"""Interface para RemoveSource command handler."""

from abc import ABC, abstractmethod

from .command import RemoveSourceCommand
from .result import RemoveSourceResult


class IRemoveRssFeedHandler(ABC):
    """Interface para handler de eliminación de fuente RSS."""

    @abstractmethod
    async def handle(self, command: RemoveSourceCommand) -> RemoveSourceResult:
        """
        Maneja el comando de eliminación de fuente RSS.

        Args:
            command: Comando con información de eliminación de la fuente

        Returns:
            RemoveSourceResult: Resultado de la operación

        Raises:
            SourceNotFoundError: Si la fuente no existe
            SourceHasActiveSessionsError: Si la fuente tiene sesiones activas
            SourceRemovalError: Si hay errores en la eliminación
        """
        pass
