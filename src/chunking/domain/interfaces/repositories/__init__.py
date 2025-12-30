"""Repository interfaces para Chunking bounded context."""

from .content_chunk_read_repository import IContentChunkReadRepository
from .content_chunk_write_repository import IContentChunkWriteRepository

__all__ = [
    "IContentChunkReadRepository",
    "IContentChunkWriteRepository",
]
