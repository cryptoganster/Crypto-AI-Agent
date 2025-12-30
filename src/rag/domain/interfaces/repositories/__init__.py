"""Repository interfaces para RAG bounded context."""

from .context_pack_read_repository import IContextPackReadRepository
from .context_pack_write_repository import IContextPackWriteRepository

__all__ = [
    "IContextPackReadRepository",
    "IContextPackWriteRepository",
]
