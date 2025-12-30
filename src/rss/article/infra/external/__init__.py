"""External adapters for Article bounded context."""

from .html_to_markdown_converter import HtmlToMarkdownConverter
from .html_to_plaintext_converter import HtmlToPlaintextConverter
from .language_detector import LanguageDetector
from .playwright_scraper_service import PlaywrightScraperService
from .trafilatura_scraper_service import TrafilaturaScraperService

__all__ = [
    "HtmlToMarkdownConverter",
    "HtmlToPlaintextConverter",
    "LanguageDetector",
    "PlaywrightScraperService",
    "TrafilaturaScraperService",
]
