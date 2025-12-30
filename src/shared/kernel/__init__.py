"""Shared kernel - Core abstractions for DDD."""

from src.shared.kernel.aggregate_root import IAggregateRoot
from src.shared.kernel.bus import IEventBus, IMediator
from src.shared.kernel.commands import ICommand, ICommandHandler
from src.shared.kernel.domain_event import IDomainEvent
from src.shared.kernel.entity import IEntity
from src.shared.kernel.errors import (
    ConcurrencyException,
    ConflictException,
    DomainException,
    EventPublishException,
    HandlerNotFoundException,
    InvalidOperationException,
    KernelException,
    NotFoundException,
    RepositoryException,
    ValidationException,
)
from src.shared.kernel.event_handler import (
    IAsyncEventHandler,
    IEventHandler,
    IEventHandlerRegistry,
)
from src.shared.kernel.logger import ILogger, LogLevel
from src.shared.kernel.queries import IQuery, IQueryHandler
from src.shared.kernel.scheduler import IAPScheduler
from src.shared.kernel.time_provider import ITimeProvider, SystemTimeProvider
from src.shared.kernel.uow import (
    ITransactionalUnitOfWork,
    IUnitOfWork,
    IUnitOfWorkFactory,
)
from src.shared.kernel.value_object import IValueObject

__all__ = [
    # Core abstractions
    "IAggregateRoot",
    "IEntity",
    "IValueObject",
    "IDomainEvent",
    "IDomainEvent",
    # CQRS
    "ICommand",
    "ICommandHandler",
    "IQuery",
    "IQueryHandler",
    # Bus patterns
    "IMediator",
    "IEventBus",
    # Event Handlers
    "IEventHandler",
    "IAsyncEventHandler",
    "IEventHandlerRegistry",
    # Logger
    "ILogger",
    "LogLevel",
    # Time Provider
    "ITimeProvider",
    "SystemTimeProvider",
    # Scheduler
    "IAPScheduler",
    # Unit of Work
    "IUnitOfWork",
    "IUnitOfWorkFactory",
    "ITransactionalUnitOfWork",
    # Exceptions
    "KernelException",
    "DomainException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    "InvalidOperationException",
    "HandlerNotFoundException",
    "EventPublishException",
    "RepositoryException",
    "ConcurrencyException",
]
