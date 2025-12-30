"""External service interfaces para Chunking bounded context."""

from .text_splitter import ITextSplitter
from .token_encoder import ITokenEncoder

__all__ = [
    "ITextSplitter",
    "ITokenEncoder",
]
