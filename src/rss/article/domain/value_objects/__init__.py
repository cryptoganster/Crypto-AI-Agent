"""Article Domain Value Objects."""

# Módulos organizados
# Quality Level (migrado a shared)
from src.shared.domain.value_objects import Level, LevelEnum

from . import analysis, metadata, similarity

# Re-exportar desde submódulos para conveniencia
from .analysis import (
    ArticleAnalysis,
    ArticleDuplicate,
    ArticleError,
    ArticleMetrics,
    ArticleQuality,
    ReadingTime,
    RssArticleError,
    RssArticleMetrics,
    WordCount,
)

# Value Objects específicos de Article
from .deduplication_result import (  # ArticleDeduplicationResult es alias
    ArticleDeduplicationResult,
    RssArticleDeduplicationResult,
)

# Scraping VOs (migrados desde src/domain/value_objects/article/scrapping)
from .javascript_domain_registry import JavaScriptDomainRegistry
from .metadata import (
    ArticleAuthor,
    ArticleCategory,
    ArticleContent,
    ArticleDescription,
    ArticleGuid,
    ArticleId,
    ArticleLanguage,
    ArticleMetadata,
    ArticlePubDate,
    ArticleSummary,
    ArticleThumbnailUrl,
    ArticleTimestamps,
    ArticleTitle,
    ArticleUrl,
    RssArticleId,
)
from .minimum_content_length import MinimumContentLength
from .readability_score import ReadabilityScore
from .scraper_type import ScraperStrategy, ScraperType
from .scraping_decision import ScrapingDecision
from .scrapped_html import ScrappedHtml
from .similarity import ContentHash, ContentHashAlgorithm
from .url_pattern_collection import UrlPatternCollection
from .validation_info import ValidationInfo

__all__ = [
    # Módulos
    "metadata",
    "analysis",
    "similarity",
    # Quality Level (shared)
    "Level",
    "LevelEnum",
    # Article-specific VOs
    "RssArticleDeduplicationResult",
    "ArticleDeduplicationResult",  # Alias para compatibilidad
    "ReadabilityScore",
    "ValidationInfo",
    "ContentHash",
    "ContentHashAlgorithm",
    # Metadata VOs
    "RssArticleId",
    "ArticleId",  # Alias para compatibilidad
    "ArticleTitle",
    "ArticleUrl",
    "ArticleAuthor",
    "ArticleCategory",
    "ArticleSummary",
    "ArticleDescription",
    "ArticleThumbnailUrl",
    "ArticleLanguage",
    "ArticleContent",
    "ArticleTimestamps",
    "ArticleGuid",
    "ArticlePubDate",
    "ArticleMetadata",
    # Analysis VOs
    "RssArticleMetrics",
    "ArticleMetrics",  # Alias para compatibilidad
    "ArticleDuplicate",
    "RssArticleError",
    "ArticleError",  # Alias para compatibilidad
    "ArticleQuality",
    "ArticleAnalysis",
    "ReadingTime",
    "WordCount",
    # Scraping VOs
    "JavaScriptDomainRegistry",
    "MinimumContentLength",
    "ScraperStrategy",
    "ScraperType",
    "ScrapingDecision",
    "ScrappedHtml",
    "UrlPatternCollection",
]
