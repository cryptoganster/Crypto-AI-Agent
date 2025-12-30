"""Interfaces para Mediator y Event Bus patterns."""

from abc import ABC, abstractmethod
from typing import Any, List, Sequence

from src.shared.kernel.domain_event import IDomainEvent


class IMediator(ABC):
    """
    Interface para Mediator pattern - coordina Commands y Queries.

    El Mediator desacopla el código que envía requests (commands/queries)
    del código que los maneja (handlers). Proporciona un punto central
    de coordinación sin acoplamiento directo.

    Beneficios CQRS:
    - Single point para routing de requests
    - Desacoplamiento entre sender y handler
    - Fácil agregar nuevos handlers sin modificar código existente
    - Facilita testing (mock del mediator)
    - Logging y auditoría centralizados

    Flujo:
    1. Cliente envía command/query al mediator
    2. Mediator encuentra el handler apropiado
    3. Handler ejecuta la lógica
    4. Mediator retorna el resultado

    Example:
        >>> # En un endpoint de API
        >>> @router.post("/articles")
        >>> async def create_article(
        ...     request: CreateArticleRequest,
        ...     mediator: IMediator = Depends(get_mediator)
        ... ):
        ...     command = CreateArticleCommand(
        ...         title=request.title,
        ...         url=request.url,
        ...         source_id=request.source_id
        ...     )
        ...     result = await mediator.send(command)
        ...     if not result.success:
        ...         raise HTTPException(400, result.error)
        ...     return ArticleResponse.from_domain(result.article)
    """

    @abstractmethod
    async def send(self, request: object) -> Any:
        """
        Envía un command o query al handler correspondiente.

        El mediator determina automáticamente el handler apropiado
        basándose en el tipo del request.

        Args:
            request: Command o Query a ejecutar

        Returns:
            Resultado del handler (tipo depende del request)

        Raises:
            HandlerNotFoundException: Si no hay handler registrado
            ValidationException: Si la validación falla
            DomainException: Si hay errores de negocio

        Example:
            >>> command = CreateArticleCommand(title="...", url="...")
            >>> result = await mediator.send(command)
            >>>
            >>> query = GetArticleQuery(article_id="123")
            >>> article_dto = await mediator.send(query)
        """
        pass

    @abstractmethod
    async def publish(self, event: IDomainEvent) -> None:
        """
        Publica un evento de dominio a todos los handlers suscritos.

        A diferencia de send() que tiene un solo handler, publish()
        puede tener múltiples handlers para el mismo evento.

        Args:
            event: Evento de dominio a publicar

        Example:
            >>> event = ArticleCreated(article_id="123", title="...")
            >>> await mediator.publish(event)
        """
        pass


class IEventBus(ABC):
    """
    Interface para Event Bus - publicación de eventos de dominio.

    El Event Bus maneja la publicación y distribución de eventos de
    dominio a los handlers apropiados. Permite comunicación asíncrona
    entre bounded contexts sin acoplamiento directo.

    Características:
    - Publicación asíncrona de eventos
    - Múltiples handlers por evento
    - Desacoplamiento entre publicador y suscriptores
    - Soporte para batch publishing
    - Garantías de entrega (at-least-once)

    Casos de uso:
    - Comunicación entre bounded contexts
    - Side effects (emails, notificaciones)
    - Auditoría y logging
    - Métricas y analytics
    - Cache invalidation
    - Sincronización de read models (CQRS)

    Example:
        >>> # En un repository después de persistir
        >>> article = Article.create(title="...", url="...")
        >>> await repository.save(article)
        >>>
        >>> # Publicar eventos generados por el aggregate
        >>> events = article.get_uncommitted_events()
        >>> await event_bus.publish_all(events)
        >>> article.mark_events_as_committed()
    """

    @abstractmethod
    async def publish(self, event: IDomainEvent) -> None:
        """
        Publica un evento de dominio individual.

        El evento será despachado a todos los handlers registrados
        para ese tipo de evento.

        Args:
            event: Evento de dominio a publicar

        Raises:
            EventPublishException: Si falla la publicación

        Example:
            >>> event = ArticlePublished(article_id="123", quality_score=0.85)
            >>> await event_bus.publish(event)
        """
        pass

    @abstractmethod
    async def publish_all(self, events: Sequence[IDomainEvent]) -> None:
        """
        Publica múltiples eventos de dominio en lote.

        Más eficiente que publicar eventos uno por uno. Garantiza
        que todos los eventos se publican en orden.

        Args:
            events: Secuencia de eventos a publicar

        Raises:
            EventPublishException: Si falla la publicación

        Example:
            >>> # Después de persistir un aggregate
            >>> article = await repository.find_by_id("123")
            >>> article.publish()
            >>> article.add_tag("python")
            >>>
            >>> await repository.save(article)
            >>>
            >>> # Publicar todos los eventos generados
            >>> events = article.get_uncommitted_events()
            >>> await event_bus.publish_all(events)
            >>> article.mark_events_as_committed()
        """
        pass

    @abstractmethod
    async def subscribe(self, event_type: type[IDomainEvent], handler: Any) -> None:
        """
        Suscribe un handler a un tipo específico de evento.

        Args:
            event_type: Tipo de evento a suscribirse
            handler: Handler que procesará el evento

        Example:
            >>> async def on_article_created(event: ArticleCreated):
            ...     logger.info(f"Article created: {event.article_id}")
            >>>
            >>> await event_bus.subscribe(ArticleCreated, on_article_created)
        """
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: type[IDomainEvent], handler: Any) -> None:
        """
        Desuscribe un handler de un tipo de evento.

        Args:
            event_type: Tipo de evento
            handler: Handler a desuscribir
        """
        pass
