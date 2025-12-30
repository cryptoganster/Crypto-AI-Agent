"""
ExtractArticleKeywords Command - Extracción especializada de keywords.

Comando CQRS puro para extraer keywords de artículos RSS usando
IArticleAnalysisService. Responsabilidad única: extracción de keywords.
"""

from .command import ExtractArticleKeywordsCommand
from .dto import (
    ExtractKeywordsRequestDto,
    ExtractKeywordsResponseDto,
    KeywordDto,
)
from .exception import (
    ArticleNotFoundError,
    InsufficientContentError,
    InvalidLanguageError,
    KeywordExtractionError,
    KeywordExtractionServiceError,
    KeywordPersistenceError,
)
from .handler import ExtractArticleKeywordsHandler
from .interface import IExtractArticleKeywordsHandler
from .result import KeywordExtractionResult
from .validator import ExtractArticleKeywordsValidator, ValidationResult

__all__ = [
    # Command y Handler
    "ExtractArticleKeywordsCommand",
    "ExtractArticleKeywordsHandler",
    "IExtractArticleKeywordsHandler",
    # Result y DTOs
    "KeywordExtractionResult",
    "ExtractKeywordsRequestDto",
    "ExtractKeywordsResponseDto",
    "KeywordDto",
    # Validator
    "ExtractArticleKeywordsValidator",
    "ValidationResult",
    # Excepciones
    "KeywordExtractionError",
    "ArticleNotFoundError",
    "InsufficientContentError",
    "KeywordExtractionServiceError",
    "KeywordPersistenceError",
    "InvalidLanguageError",
]
