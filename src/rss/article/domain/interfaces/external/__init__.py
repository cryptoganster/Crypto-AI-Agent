"""Interfaces para servicios externos de Article bounded context."""

from .html_to_markdown_converter import IHtmlToMarkdownConverter
from .html_to_plaintext_converter import IHtmlToPlaintextConverter
from .language_detector import ILanguageDetector, LanguageDetectionResult
from .scraping_service import IArticleScrapingService

__all__ = [
    "IArticleScrapingService",
    "IHtmlToMarkdownConverter",
    "IHtmlToPlaintextConverter",
    "ILanguageDetector",
    "LanguageDetectionResult",
]
