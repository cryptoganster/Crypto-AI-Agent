"""Repository interfaces para clustering."""

from .semantic_cluster_read_repository import ISemanticClusterReadRepository
from .semantic_cluster_write_repository import ISemanticClusterWriteRepository

__all__ = [
    "ISemanticClusterReadRepository",
    "ISemanticClusterWriteRepository",
]
