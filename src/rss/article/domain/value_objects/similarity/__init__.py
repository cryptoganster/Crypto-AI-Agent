"""
Value Objects para análisis de similitud.

Encapsula conceptos relacionados con similitud y hashing de contenido.
"""

from .content_hash import ContentHash, ContentHashAlgorithm

__all__ = [
    "ContentHash",
    "ContentHashAlgorithm",
]
