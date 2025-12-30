"""Interface para ActivateSource command handler - CQRS."""

from abc import ABC, abstractmethod

from .command import ActivateSourceCommand
from .result import ActivateSourceResult


class IActivateRssFeedHandler(ABC):
    """Interface CQRS para handler de activación de fuentes RSS usando Source aggregate."""

    @abstractmethod
    async def handle(self, command: ActivateSourceCommand) -> ActivateSourceResult:
        """
        Maneja el comando de activación de fuente RSS.

        Args:
            command: Comando con información de activación de la fuente

        Returns:
            ActivateSourceResult: Resultado de la operación

        Raises:
            SourceNotFoundError: Si la fuente no existe
            SourceAlreadyActiveError: Si la fuente ya está activa
            SourceHealthCheckFailedError: Si el health check falla
        """
        pass
