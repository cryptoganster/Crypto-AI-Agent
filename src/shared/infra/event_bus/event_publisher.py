"""Implementación del publicador de eventos de dominio con logging."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.shared.kernel import IDomainEvent, IEventBus
from src.shared.kernel.logger import ILogger

# Type alias para compatibilidad
Event = IDomainEvent


class EventPublisher(IEventBus):
    """
    Implementación del publicador de eventos usando logging estructurado.

    Esta implementación usa Loguru para registrar todos los eventos
    de dominio de forma estructurada. En el futuro se puede extender para
    usar message brokers como RabbitMQ o Apache Kafka.
    """

    def __init__(
        self,
        logger: Optional[ILogger] = None,
        log_events: bool = True,
        structured_logging: bool = True,
        batch_size: int = 100,
    ):
        """
        Inicializar el publicador.

        Args:
            logger: Logger para registrar eventos
            log_events: Si registrar eventos en logs
            structured_logging: Si usar logging estructurado JSON
            batch_size: Tamaño máximo de lote para publicación
        """
        from src.shared.config.logging_config import LoggingConfig
        from src.shared.infra.logger.loguru_service import (
            LoguruService,
        )

        self._logger = logger or LoguruService(LoggingConfig())
        self.log_events = log_events
        self.structured_logging = structured_logging
        self.batch_size = batch_size

        # Estadísticas internas
        self._published_count = 0
        self._failed_count = 0
        self._last_publish_at: Optional[datetime] = None

        # Buffer para batch processing
        self._event_buffer: List[Event] = []
        self._buffer_lock = asyncio.Lock()

        self._logger.info("EventPublisher inicializado")

    # Métodos requeridos por IEventBus interface
    async def publish(self, event: IDomainEvent) -> None:
        """Publica un evento de dominio individual (método requerido por interface)."""
        await self.publish_event(event)

    async def publish_batch(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos de dominio en lote (método requerido por interface)."""
        await self.publish_events(events)

    async def publish_and_wait(
        self, event: IDomainEvent, timeout_seconds: float = 30.0
    ) -> None:
        """Publica un evento y espera confirmación (método requerido por interface)."""
        # Para la implementación de logging, simplemente publicamos el evento
        # En implementaciones futuras con message brokers, aquí esperaríamos confirmación
        await self.publish_event(event)

    # Métodos adicionales requeridos por IEventBus interface
    async def publish_all(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos de dominio en lote (método requerido por IEventBus)."""
        await self.publish_events(events)

    async def subscribe(self, event_type: type[IDomainEvent], handler: Any) -> None:
        """
        Suscribe un handler a un tipo específico de evento.

        Nota: Esta implementación básica no soporta suscripción dinámica.
        Para soporte completo de event handlers, usar EventPublisherWithDispatch.
        """
        self._logger.warning(
            f"subscribe() llamado pero no implementado en EventPublisher básico. "
            f"Usar EventPublisherWithDispatch para soporte de handlers."
        )

    async def unsubscribe(self, event_type: type[IDomainEvent], handler: Any) -> None:
        """
        Desuscribe un handler de un tipo de evento.

        Nota: Esta implementación básica no soporta suscripción dinámica.
        Para soporte completo de event handlers, usar EventPublisherWithDispatch.
        """
        self._logger.warning(
            f"unsubscribe() llamado pero no implementado en EventPublisher básico. "
            f"Usar EventPublisherWithDispatch para soporte de handlers."
        )

    async def publish_event(self, event: Event) -> None:
        """
        Publicar un evento de dominio individual.

        Args:
            event: Evento a publicar
        """
        try:
            await self._process_single_event(event)
            self._published_count += 1
            self._last_publish_at = datetime.now(timezone.utc)

        except Exception as e:
            self._failed_count += 1
            if self._logger:
                self._logger.error(f"Error publicando evento {event.event_id}: {e}")
            raise

    async def publish_events(self, events: List[Event]) -> None:
        """
        Publicar múltiples eventos de dominio.

        Args:
            events: Lista de eventos a publicar
        """
        if not events:
            return

        try:
            await self._process_batch_events(events)
            self._published_count += len(events)
            self._last_publish_at = datetime.now(timezone.utc)

        except Exception as e:
            self._failed_count += len(events)
            if self._logger:
                self._logger.error(
                    f"Error publicando lote de {len(events)} eventos: {e}"
                )

    async def publish_events_async(self, events: List[Event]) -> None:
        """
        Publicar eventos de forma asíncrona sin bloquear.

        Args:
            events: Lista de eventos a publicar
        """
        if not events:
            return

        # Agregar eventos al buffer para procesamiento asíncrono
        async with self._buffer_lock:
            self._event_buffer.extend(events)

            # Si el buffer está lleno, procesar inmediatamente
            if len(self._event_buffer) >= self.batch_size:
                events_to_process = self._event_buffer[: self.batch_size]
                self._event_buffer = self._event_buffer[self.batch_size :]

                # Procesar en background task
                asyncio.create_task(self._process_batch_events(events_to_process))

    async def flush_pending_events(self) -> int:
        """
        Procesar todos los eventos pendientes en el buffer.

        Returns:
            Número de eventos procesados
        """
        async with self._buffer_lock:
            if not self._event_buffer:
                return 0

            events_to_process = self._event_buffer.copy()
            self._event_buffer.clear()

        await self._process_batch_events(events_to_process)
        return len(events_to_process)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del publicador.

        Returns:
            Dict con estadísticas de publicación
        """
        return {
            "published_count": self._published_count,
            "failed_count": self._failed_count,
            "success_rate": (
                self._published_count / (self._published_count + self._failed_count)
                if (self._published_count + self._failed_count) > 0
                else 0.0
            ),
            "last_publish_at": (
                self._last_publish_at.isoformat() if self._last_publish_at else None
            ),
            "pending_events": len(self._event_buffer),
            "batch_size": self.batch_size,
        }

    async def _process_single_event(self, event: Event) -> None:
        """Procesar un evento individual."""
        if not self.log_events:
            return

        event_data = self._serialize_event(event)

        if self.structured_logging:
            # Logging estructurado con contexto completo
            if self._logger:
                self._logger.bind(
                    event_id=event.event_id,
                    event_type=event.__class__.__name__,
                    aggregate_id=getattr(event, "aggregate_id", None),
                    occurred_at=event.occurred_at.isoformat(),
                    event_data=event_data,
                ).info(f"Domain Event: {event.__class__.__name__}")
        else:
            # Log simple
            if self._logger:
                self._logger.info(
                    f"Domain Event Published: {event.__class__.__name__} [{event.event_id}]"
                )

    async def _process_batch_events(self, events: List[Event]) -> None:
        """Procesar un lote de eventos."""
        if not self.log_events or not events:
            return

        # Agrupar por tipo de evento
        events_by_type = {}
        for event in events:
            event_type = event.__class__.__name__
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)

        # Log resumen del lote
        if self._logger:
            self._logger.info(f"Processing batch of {len(events)} domain events")

            for event_type, type_events in events_by_type.items():
                self._logger.info(f"  - {event_type}: {len(type_events)} events")

        # Procesar cada evento
        for event in events:
            await self._process_single_event(event)

        # Log de finalización
        if self._logger:
            self._logger.info(
                f"Batch processing completed: {len(events)} events published"
            )

    def _serialize_event(self, event: Event) -> Dict[str, Any]:
        """
        Serializar evento para logging estructurado.

        Args:
            evento: Evento a serializar

        Returns:
            Dict con datos serializables (sin métodos)
        """
        try:
            # Obtener todos los atributos públicos del evento
            event_dict = {}

            for attr_name in dir(event):
                if not attr_name.startswith("_") and attr_name != "occurred_at":
                    try:
                        attr_value = getattr(event, attr_name)

                        # Excluir callables (métodos) que causan PicklingError
                        if callable(attr_value):
                            continue

                        # Solo incluir valores serializables
                        if self._is_serializable(attr_value):
                            event_dict[attr_name] = attr_value
                    except (AttributeError, TypeError):
                        continue

            return event_dict

        except Exception as e:
            if self._logger:
                self._logger.warning(
                    f"Error serializando evento {event.__class__.__name__}: {e}"
                )
            return {"error": f"Serialization failed: {str(e)}"}

    def _is_serializable(self, value: Any) -> bool:
        """Verificar si un valor es serializable a JSON."""
        try:
            json.dumps(value, default=str)
            return True
        except (TypeError, ValueError):
            return False


# Factory para crear publicadores según configuración
def create_event_publisher(
    publisher_type: str = "logging",
    with_event_handlers: bool = False,
    event_handler_registry=None,
    logger=None,
) -> IEventBus:
    """
    Factory para crear instancias del publicador con configuración avanzada.

    Args:
        publisher_type: Tipo de publicador ('logging', 'memory')
        with_event_handlers: Si incluir dispatch automático a event handlers
        event_handler_registry: Registry de handlers (requerido si with_event_handlers=True)
        logger: Logger personalizado

    Returns:
        Instancia del publicador configurado
    """
    if publisher_type == "logging":
        base_publisher = EventPublisher(logger=logger)

        if with_event_handlers:
            if not event_handler_registry:
                raise ValueError(
                    "event_handler_registry es requerido cuando with_event_handlers=True"
                )

            from src.shared.infra.event_bus.event_publisher_with_dispatch import (
                EventPublisherWithDispatch,
            )

            return EventPublisherWithDispatch(
                base_publisher, event_handler_registry, logger or base_publisher._logger
            )

        return base_publisher

    elif publisher_type == "memory":
        from src.shared.infra.event_bus.in_memory_event_publisher import (
            InMemoryEventPublisher,
        )

        return InMemoryEventPublisher()

    else:
        raise ValueError(f"Tipo de publicador no soportado: {publisher_type}")


# Instancia global por defecto
_default_publisher: Optional[IEventBus] = None


def get_event_publisher() -> IEventBus:
    """
    Obtener instancia global del publicador.

    Returns:
        Publicador configurado
    """
    global _default_publisher

    if _default_publisher is None:
        _default_publisher = create_event_publisher("logging")

    return _default_publisher


def set_event_publisher(publisher: IEventBus) -> None:
    """
    Configurar publicador global.

    Args:
        publisher: Nueva instancia del publicador
    """
    global _default_publisher
    _default_publisher = publisher


# Legacy compatibility aliases - DEPRECATED
LoggingDomainEventPublisher = EventPublisher
create_domain_event_publisher = create_event_publisher
get_domain_event_publisher = get_event_publisher
set_domain_event_publisher = set_event_publisher
