"""DetectArticleLanguage Command - Detección de idioma de artículos."""

from .command import DetectArticleLanguageCommand
from .dto import DetectArticleLanguageRequestDto, DetectArticleLanguageResponseDto
from .exception import (
    ArticleNotFoundError,
    DetectionServiceError,
    InsufficientContentError,
    LanguageDetectionError,
    LanguagePersistenceError,
)
from .handler import DetectArticleLanguageHandler
from .interface import IDetectArticleLanguageHandler
from .result import LanguageDetectionResult
from .validator import DetectArticleLanguageValidator, ValidationResult

__all__ = [
    # Command
    "DetectArticleLanguageCommand",
    # Handler
    "DetectArticleLanguageHandler",
    "IDetectArticleLanguageHandler",
    # Result
    "LanguageDetectionResult",
    # Validator
    "DetectArticleLanguageValidator",
    "ValidationResult",
    # DTOs
    "DetectArticleLanguageRequestDto",
    "DetectArticleLanguageResponseDto",
    # Exceptions
    "LanguageDetectionError",
    "ArticleNotFoundError",
    "InsufficientContentError",
    "DetectionServiceError",
    "LanguagePersistenceError",
]
