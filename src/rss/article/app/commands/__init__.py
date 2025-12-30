"""Article Application Commands.

Este módulo contiene todos los comandos (CQRS write side) para el bounded context de Article.
"""

from .calculate_metrics import (
    CalculateArticleMetricsCommand,
    CalculateArticleMetricsHandler,
    ICalculateArticleMetricsHandler,
)
from .calculate_quality import (
    CalculateArticleQualityCommand,
    CalculateArticleQualityHandler,
    ICalculateArticleQualityHandler,
)
from .convert_to_markdown import (
    ConvertArticleToMarkdownCommand,
    ConvertArticleToMarkdownHandler,
    IConvertArticleToMarkdownHandler,
)
from .detect_language import (
    DetectArticleLanguageCommand,
    DetectArticleLanguageHandler,
    IDetectArticleLanguageHandler,
)
from .extract_keywords import (
    ExtractArticleKeywordsCommand,
    ExtractArticleKeywordsHandler,
    IExtractArticleKeywordsHandler,
)
from .extract_plaintext import (
    ExtractArticlePlaintextCommand,
    ExtractArticlePlaintextHandler,
    IExtractArticlePlaintextHandler,
)
from .generate_summary import (
    GenerateArticleSummaryCommand,
    GenerateArticleSummaryHandler,
    IGenerateArticleSummaryHandler,
)
from .scrape_content import (
    IScrapeArticleContentHandler,
    ScrapeArticleContentCommand,
    ScrapeArticleContentHandler,
)

__all__ = [
    # Calculate Metrics
    "CalculateArticleMetricsCommand",
    "CalculateArticleMetricsHandler",
    "ICalculateArticleMetricsHandler",
    # Calculate Quality
    "CalculateArticleQualityCommand",
    "CalculateArticleQualityHandler",
    "ICalculateArticleQualityHandler",
    # Convert to Markdown
    "ConvertArticleToMarkdownCommand",
    "ConvertArticleToMarkdownHandler",
    "IConvertArticleToMarkdownHandler",
    # Detect Language
    "DetectArticleLanguageCommand",
    "DetectArticleLanguageHandler",
    "IDetectArticleLanguageHandler",
    # Extract Keywords
    "ExtractArticleKeywordsCommand",
    "ExtractArticleKeywordsHandler",
    "IExtractArticleKeywordsHandler",
    # Extract Plaintext
    "ExtractArticlePlaintextCommand",
    "ExtractArticlePlaintextHandler",
    "IExtractArticlePlaintextHandler",
    # Generate Summary
    "GenerateArticleSummaryCommand",
    "GenerateArticleSummaryHandler",
    "IGenerateArticleSummaryHandler",
    # Scrape Content
    "ScrapeArticleContentCommand",
    "ScrapeArticleContentHandler",
    "IScrapeArticleContentHandler",
]
