"""UpdateSource command - Actualización de Source aggregate."""

from .command import UpdateSourceCommand
from .exception import (
    InvalidSourceUpdateError,
    SourceConfigurationError,
    SourceNotFoundError,
    UpdateSourceError,
)
from .handler import UpdateSourceHandler
from .result import UpdateSourceResult
from .validator import UpdateSourceValidator

try:
    from .interface import IUpdateSourceHandler

    __all__ = [
        "UpdateSourceCommand",
        "UpdateSourceHandler",
        "UpdateSourceResult",
        "UpdateSourceValidator",
        "IUpdateSourceHandler",
        "UpdateSourceError",
        "SourceNotFoundError",
        "InvalidSourceUpdateError",
        "SourceConfigurationError",
    ]
except ImportError:
    __all__ = [
        "UpdateSourceCommand",
        "UpdateSourceHandler",
        "UpdateSourceResult",
        "UpdateSourceValidator",
        "UpdateSourceError",
        "SourceNotFoundError",
        "InvalidSourceUpdateError",
        "SourceConfigurationError",
    ]
