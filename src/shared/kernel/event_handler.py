"""Interfaces para Event Handlers en arquitectura event-driven."""

from abc import ABC, abstractmethod
from typing import Generic, List, Type, TypeVar

from src.shared.kernel.domain_event import IDomainEvent

TEvent = TypeVar("TEvent", bound=IDomainEvent)


class IEventHandler(ABC, Generic[TEvent]):
    """
    Interface base para handlers de eventos de dominio.

    Los event handlers reaccionan a eventos específicos y ejecutan
    lógica de side effects (notificaciones, métricas, cache invalidation, etc.)
    """

    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        """
        Procesa un evento de dominio específico.

        Args:
            event: Evento a procesar

        Raises:
            Exception: Si hay errores durante el procesamiento
        """
        pass

    @property
    @abstractmethod
    def event_type(self) -> Type[TEvent]:
        """Tipo de evento que maneja este handler."""
        pass


class IEventHandlerRegistry(ABC):
    """
    Registry para gestionar event handlers de forma centralizada.

    Permite registro automático de handlers y dispatch de eventos
    a los handlers apropiados.
    """

    @abstractmethod
    def register_handler(
        self, event_type: Type[IDomainEvent], handler: IEventHandler
    ) -> None:
        """
        Registra un handler para un tipo específico de evento.

        Args:
            event_type: Tipo de evento
            handler: Handler que procesará el evento
        """
        pass

    @abstractmethod
    def get_handlers(self, event_type: Type[IDomainEvent]) -> List[IEventHandler]:
        """
        Obtiene todos los handlers registrados para un tipo de evento.

        Args:
            event_type: Tipo de evento

        Returns:
            Lista de handlers registrados
        """
        pass

    @abstractmethod
    async def dispatch_event(self, event: IDomainEvent) -> None:
        """
        Despacha un evento a todos sus handlers registrados.

        Args:
            event: Evento a procesar
        """
        pass

    @abstractmethod
    async def dispatch_events(self, events: List[IDomainEvent]) -> None:
        """
        Despacha múltiples eventos en lote.

        Args:
            events: Lista de eventos a procesar
        """
        pass


class IAsyncEventHandler(ABC, Generic[TEvent]):
    """
    Interface para handlers asíncronos que no bloquean la transacción principal.

    Útil para operaciones que pueden fallar sin afectar la consistencia:
    - Envío de emails
    - Notificaciones push
    - Llamadas a APIs externas
    - Métricas y analytics
    """

    @abstractmethod
    async def handle_async(self, event: TEvent) -> None:
        """
        Procesa evento de forma asíncrona sin bloquear.

        Args:
            event: Evento a procesar asincrónicamente
        """
        pass

    @property
    @abstractmethod
    def event_type(self) -> Type[TEvent]:
        """Tipo de evento que maneja este handler."""
        pass

    @property
    @abstractmethod
    def max_retries(self) -> int:
        """Número máximo de reintentos en caso de fallo."""
        pass
