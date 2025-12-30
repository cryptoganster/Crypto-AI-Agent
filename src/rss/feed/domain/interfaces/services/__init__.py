"""Interfaces para Domain Services del bounded context Source."""

from .health import ISourceHealthService
from .metrics_calculation import ISourceMetricsCalculationService
from .rss_content_cleanup_service import CleanupSummary, IRssContentCleanupService
from .similarity import ISourceSimilarityService
from .validation import ISourceValidationService

__all__ = [
    "CleanupSummary",
    "ISourceHealthService",
    "ISourceMetricsCalculationService",
    "IRssContentCleanupService",
    "ISourceSimilarityService",
    "ISourceValidationService",
]
