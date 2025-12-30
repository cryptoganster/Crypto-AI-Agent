"""Interfaces del bounded context Clustering."""

from .cluster_repository import IClusterReadRepository, IClusterWriteRepository

__all__ = [
    "IClusterReadRepository",
    "IClusterWriteRepository",
]
