"""Extract Article Plaintext Command - Extrae texto plano desde HTML."""

from .command import ExtractArticlePlaintextCommand
from .exception import (
    ArticleNotFoundError,
    NoScrapedContentError,
    PlaintextConversionError,
    PlaintextExtractionError,
)
from .handler import ExtractArticlePlaintextHandler
from .interface import IExtractArticlePlaintextHandler
from .result import PlaintextExtractionResult

__all__ = [
    "ExtractArticlePlaintextCommand",
    "ExtractArticlePlaintextHandler",
    "IExtractArticlePlaintextHandler",
    "PlaintextExtractionResult",
    "PlaintextExtractionError",
    "ArticleNotFoundError",
    "NoScrapedContentError",
    "PlaintextConversionError",
]
