"""Query Handlers para Article bounded context (CQRS Read Side).

CQRS Estricto:
- Queries solo leen, no modifican estado
- Cada query tiene su propio handler
- DTOs inline en result.py
- Naming: get_* (no find_*)
"""

from .get_by_id import (
    ArticleDTO,
    GetArticleByIdHandler,
    GetArticleByIdQuery,
    GetArticleByIdResult,
)
from .get_pending import (
    GetPendingArticlesHandler,
    GetPendingArticlesQuery,
    GetPendingArticlesResult,
    PendingArticleDTO,
)
from .get_publishing_readiness import (
    ArticleReadinessDTO,
    GetPublishingReadinessHandler,
    GetPublishingReadinessQuery,
    PublishingReadinessDTO,
    ReadinessSummaryDTO,
)
from .get_quality_metrics import (
    GetQualityMetricsHandler,
    GetQualityMetricsQuery,
    QualityMetricsDTO,
)
from .get_stats import (
    ArticleStatsDTO,
    GetArticleStatsHandler,
    GetArticleStatsQuery,
    TimelineDataPoint,
)

__all__ = [
    # get_article_by_id
    "GetArticleByIdQuery",
    "GetArticleByIdHandler",
    "GetArticleByIdResult",
    "ArticleDTO",
    # get_pending_articles
    "GetPendingArticlesQuery",
    "GetPendingArticlesHandler",
    "GetPendingArticlesResult",
    "PendingArticleDTO",
    # get_publishing_readiness
    "GetPublishingReadinessQuery",
    "GetPublishingReadinessHandler",
    "PublishingReadinessDTO",
    "ArticleReadinessDTO",
    "ReadinessSummaryDTO",
    # get_quality_metrics
    "GetQualityMetricsQuery",
    "GetQualityMetricsHandler",
    "QualityMetricsDTO",
    # get_stats
    "GetArticleStatsQuery",
    "GetArticleStatsHandler",
    "ArticleStatsDTO",
    "TimelineDataPoint",
]
