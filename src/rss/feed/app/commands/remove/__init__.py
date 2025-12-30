"""RemoveSource Command - Remove Source."""

from .command import RemoveSourceCommand
from .handler import RemoveSourceHandler
from .result import RemoveSourceResult

try:
    from .interface import IRemoveSourceHandler

    __all__ = [
        "RemoveSourceCommand",
        "RemoveSourceHandler",
        "RemoveSourceResult",
        "IRemoveSourceHandler",
    ]
except ImportError:
    __all__ = [
        "RemoveSourceCommand",
        "RemoveSourceHandler",
        "RemoveSourceResult",
    ]
