"""Source Commands - CQRS Command Handlers."""

from .activate_source import (
    ActivateSourceCommand,
    ActivateSourceHandler,
    ActivateSourceResult,
)
from .create_source import (
    CreateSourceCommand,
    CreateSourceCommandHandler,
    CreateSourceResult,
)
from .remove_source import (
    RemoveSourceCommand,
    RemoveSourceHandler,
    RemoveSourceResult,
)
from .update_source import (
    UpdateSourceCommand,
    UpdateSourceHandler,
    UpdateSourceResult,
)

__all__ = [
    # Activate Source
    "ActivateSourceCommand",
    "ActivateSourceHandler",
    "ActivateSourceResult",
    # Create Source
    "CreateSourceCommand",
    "CreateSourceCommandHandler",
    "CreateSourceResult",
    # Remove Source
    "RemoveSourceCommand",
    "RemoveSourceHandler",
    "RemoveSourceResult",
    # Update Source
    "UpdateSourceCommand",
    "UpdateSourceHandler",
    "UpdateSourceResult",
]
