"""Domain Services para Article bounded context."""

# NUEVO: Nombre correcto para el servicio de generación de summaries
# DEPRECATED: Mantener temporalmente para compatibilidad durante migración
from .content_extraction import ArticleContentExtractionService
from .language_detection import ArticleLanguageDetectionService
from .metrics_calculation import ArticleMetricsCalculationService
from .plaintext_extraction import ArticlePlaintextExtractionService
from .semantic_deduplication import DuplicateMatch, SemanticDeduplicationService
from .sentence_relevance_scorer import ScoredSentence, SentenceRelevanceScorer
from .smart_scraper import SmartScraperService
from .summary_extraction import ArticleSummaryExtractionService

__all__ = [
    # NUEVO: Nombre correcto
    "ArticleSummaryExtractionService",
    # DEPRECATED: Mantener temporalmente
    "ArticleContentExtractionService",
    "ArticleLanguageDetectionService",
    "ArticleMetricsCalculationService",
    "ArticlePlaintextExtractionService",
    "ScoredSentence",
    "SentenceRelevanceScorer",
    "SmartScraperService",
    "SemanticDeduplicationService",
    "DuplicateMatch",
]
