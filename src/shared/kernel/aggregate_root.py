"""Interface base para Aggregate Roots en Domain-Driven Design."""

from abc import ABC, abstractmethod
from typing import Generic, List, Sequence, TypeVar

from src.shared.kernel.domain_event import IDomainEvent
from src.shared.kernel.entity import IEntity

EntityId = TypeVar("EntityId")
EventType = TypeVar("EventType", bound=IDomainEvent)


class IAggregateRoot(IEntity[EntityId], ABC, Generic[EntityId]):
    """
    Interface base para Aggregate Roots en DDD.

    Un Aggregate Root es la única entidad del agregado que puede ser
    referenciada desde fuera. Gestiona la consistencia del agregado
    y los eventos de dominio.

    Responsabilidades:
    - Mantener lista de eventos de dominio pendientes
    - Proporcionar acceso a eventos no confirmados
    - Marcar eventos como confirmados después de publicación

    Esta interface NO incluye:
    - Event Sourcing (load_from_history, replay_events)
    - Optimistic locking (version, increment_version)
    - Snapshots (create_snapshot, load_from_snapshot)

    Estas funcionalidades pueden agregarse en el futuro si se necesitan.

    Implementación por defecto:
    - Inicializa listas de eventos en __init__
    - Proporciona _add_domain_event() para uso interno
    - Implementa métodos de conveniencia

    """

    def __init__(self) -> None:
        """
        Inicializa el aggregate root con listas de eventos vacías.

        Los aggregates hijos deben llamar super().__init__() PRIMERO
        antes de inicializar sus propios atributos.
        """
        super().__init__()
        self._domain_events: List[IDomainEvent] = []
        self._uncommitted_events: List[IDomainEvent] = []

    @property
    def domain_events(self) -> Sequence[IDomainEvent]:
        """
        Lista de eventos de dominio pendientes de publicar.

        Solo lectura desde el exterior. Los eventos se generan cuando
        ocurren cambios significativos en el agregado.

        Returns:
            Secuencia inmutable de eventos pendientes
        """
        return tuple(self._domain_events)

    def get_uncommitted_events(self) -> Sequence[IDomainEvent]:
        """
        Obtiene eventos de dominio no confirmados.

        Utilizado por el repositorio para publicar eventos después
        de persistir el agregado. Los eventos deben publicarse de
        manera atómica con la persistencia.

        Returns:
            Secuencia de eventos pendientes de confirmar
        """
        return tuple(self._uncommitted_events)

    def mark_events_as_committed(self) -> None:
        """
        Marca todos los eventos como confirmados/publicados.

        Limpia la lista de eventos pendientes. Debe llamarse después
        de que los eventos hayan sido publicados exitosamente al event bus.

        Note:
            Este método debe ser idempotente. Llamarlo múltiples veces
            no debe causar efectos secundarios.
        """
        self._uncommitted_events.clear()

    def has_uncommitted_events(self) -> bool:
        """
        Indica si hay eventos pendientes de confirmar.

        Método de conveniencia que verifica si existen eventos
        no confirmados sin necesidad de obtener la lista completa.

        Returns:
            True si hay eventos pendientes, False en caso contrario
        """
        return len(self._uncommitted_events) > 0

    def get_event_count(self) -> int:
        """
        Obtiene el número de eventos pendientes.

        Método de conveniencia para obtener el conteo de eventos
        sin necesidad de iterar sobre la lista completa.

        Returns:
            Cantidad de eventos no confirmados
        """
        return len(self._uncommitted_events)

    def _add_domain_event(self, event: IDomainEvent) -> None:
        """
        Agrega un evento de dominio a las listas de eventos pendientes.

        Método protegido para uso interno del aggregate. Los eventos
        se agregan tanto a domain_events (historial completo) como a
        uncommitted_events (pendientes de publicar).

        Args:
            event: Evento de dominio a agregar

        Example:
            >>> self._add_domain_event(ArticleCreated(article_id=str(self.id)))
        """
        self._domain_events.append(event)
        self._uncommitted_events.append(event)
