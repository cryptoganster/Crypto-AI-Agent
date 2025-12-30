"""Excepciones específicas del Article bounded context."""

from .article_exceptions import EmptyStringException, InvalidScoreException

__all__ = [
    "InvalidScoreException",
    "EmptyStringException",
]
