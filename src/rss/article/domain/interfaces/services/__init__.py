"""Service interfaces para Article bounded context."""

# NUEVO: Nombre correcto para la interface de generación de summaries
# DEPRECATED: Mantener temporalmente para compatibilidad durante migración
from .content_extraction import IArticleContentExtractionService
from .deduplication import IArticleDeduplicationService
from .hashing import IArticleHashingService
from .keyword import IArticleKeywordService
from .language_detection import IArticleLanguageDetectionService
from .metrics_calculation import IArticleMetricsCalculationService
from .plaintext_extraction import IArticlePlaintextExtractionService
from .quality import IArticleQualityService
from .readability import IArticleReadabilityService
from .smart_scraper import ISmartScraperService
from .summary_extraction import IArticleSummaryExtractionService

__all__ = [
    # NUEVO: Nombre correcto
    "IArticleSummaryExtractionService",
    # DEPRECATED: Mantener temporalmente
    "IArticleContentExtractionService",
    "IArticleDeduplicationService",
    "IArticleHashingService",
    "IArticleKeywordService",
    "IArticleLanguageDetectionService",
    "IArticleMetricsCalculationService",
    "IArticlePlaintextExtractionService",
    "IArticleQualityService",
    "IArticleReadabilityService",
    "ISmartScraperService",
]
