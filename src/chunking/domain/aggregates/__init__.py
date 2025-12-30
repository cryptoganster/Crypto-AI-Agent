"""Aggregates del bounded context Chunking."""

from .chunk import KnowledgeChunk

# Alias for backward compatibility
ContentChunk = KnowledgeChunk

__all__ = ["KnowledgeChunk", "ContentChunk"]
