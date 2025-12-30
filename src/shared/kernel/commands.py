"""Interfaces para Command pattern en CQRS."""

from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar

# Type variables para Command y Result
TCommand = TypeVar("TCommand")
TResult = TypeVar("TResult")


class ICommand(Protocol):
    """
    Interface marker para Commands en CQRS.

    Los Commands representan intenciones de cambiar el estado del sistema.
    Son objetos inmutables que encapsulan todos los datos necesarios
    para ejecutar una operación de escritura.

    Características:
    - Inmutables (usar @dataclass(frozen=True))
    - Nombrados con verbos imperativos (CreateArticle, UpdateSource)
    - Contienen solo datos, sin lógica de negocio
    - Retornan un resultado que indica éxito/fallo

    Example:
        >>> @dataclass(frozen=True)
        >>> class CreateArticleCommand:
        ...     title: str
        ...     url: str
        ...     source_id: str
    """

    pass


class ICommandHandler(ABC, Generic[TCommand, TResult]):
    """
    Interface base para Command Handlers en CQRS.

    Los Command Handlers contienen la lógica de orquestación para ejecutar
    un comando específico. Coordinan entre aggregates, repositories y
    domain services para completar la operación.

    Responsabilidades:
    - Validar el comando (validaciones de aplicación)
    - Cargar aggregates necesarios desde repositories
    - Ejecutar lógica de negocio en aggregates
    - Persistir cambios
    - Publicar eventos de dominio
    - Retornar resultado

    Principios:
    - Un handler por comando (Single Responsibility)
    - No contiene lógica de negocio (eso va en aggregates)
    - Maneja transacciones y coordinación
    - Usa dependency injection para repositories y services

    Example:
        >>> class CreateArticleHandler(ICommandHandler[CreateArticleCommand, CreateArticleResult]):
        ...     def __init__(self, repository: IArticleRepository, event_bus: IEventBus):
        ...         self._repository = repository
        ...         self._event_bus = event_bus
        ...
        ...     async def handle(self, command: CreateArticleCommand) -> CreateArticleResult:
        ...         article = Article.create(command.title, command.url)
        ...         await self._repository.save(article)
        ...         await self._event_bus.publish_all(article.get_uncommitted_events())
        ...         return CreateArticleResult.success(article)
    """

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """
        Ejecuta el comando y retorna el resultado.

        Args:
            command: Comando a ejecutar

        Returns:
            Resultado de la ejecución (éxito o fallo)

        Raises:
            DomainException: Si hay errores de negocio
            ValidationException: Si la validación falla
        """
        pass
