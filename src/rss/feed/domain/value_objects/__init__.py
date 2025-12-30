"""RSS Feed Value Objects Package."""

from .article_filter_criteria import ArticleFilterCriteria
from .configuration import (  # SourceConfiguration es alias
    RssFeedConfiguration,
    SourceConfiguration,
)
from .content_quality import ContentQuality
from .description import (  # SourceDescription es alias
    RssFeedDescription,
    SourceDescription,
)
from .metrics import FetchData, RssFeedMetrics, SourceMetrics  # SourceMetrics es alias
from .metrics_threshold import MetricsThreshold
from .name import RssFeedName, SourceName  # SourceName es alias
from .performance_trend import PerformanceTrend, TrendDirection
from .rss_feed_id import RssFeedId, SourceId  # SourceId es alias
from .rss_feed_url import RssFeedUrl, SourceUrl
from .source_health import RssFeedHealth, SourceHealth  # SourceHealth es alias
from .source_identity import RssFeedIdentity, SourceIdentity  # SourceIdentity es alias
from .source_metadata import RssFeedMetadata, SourceMetadata  # SourceMetadata es alias
from .status import RssFeedStatus, SourceStatus  # SourceStatus es alias

__all__ = [
    # Nuevos nombres (preferidos)
    "RssFeedConfiguration",
    "RssFeedDescription",
    "RssFeedHealth",
    "RssFeedId",
    "RssFeedIdentity",
    "RssFeedMetadata",
    "RssFeedMetrics",
    "RssFeedName",
    "RssFeedStatus",
    "RssFeedUrl",
    # Aliases para compatibilidad hacia atrás
    "SourceUrl",
    "SourceConfiguration",
    "SourceDescription",
    "SourceHealth",
    "SourceId",
    "SourceIdentity",
    "SourceMetadata",
    "SourceMetrics",
    "SourceName",
    "SourceStatus",
    # Otros Value Objects
    "ArticleFilterCriteria",
    "ContentQuality",
    "FetchData",
    "MetricsThreshold",
    "PerformanceTrend",
    "TrendDirection",
]
