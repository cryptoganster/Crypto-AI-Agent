"""ActivateSource Command - Activate Source."""

from .command import ActivateSourceCommand
from .handler import ActivateSourceHandler
from .result import ActivateSourceResult

try:
    from .interface import IActivateSourceHandler

    __all__ = [
        "ActivateSourceCommand",
        "ActivateSourceHandler",
        "ActivateSourceResult",
        "IActivateSourceHandler",
    ]
except ImportError:
    __all__ = [
        "ActivateSourceCommand",
        "ActivateSourceHandler",
        "ActivateSourceResult",
    ]
