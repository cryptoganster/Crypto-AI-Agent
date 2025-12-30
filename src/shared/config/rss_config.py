"""RSS configuration."""

import os
from dataclasses import dataclass


@dataclass
class RssConfig:
    """Configuración específica para el sistema RSS y deduplicación."""

    # Deduplication
    auto_deduplication_enabled: bool = True
    deduplication_batch_size: int = 50
    deduplication_similarity_threshold: float = 0.98

    # Fetch
    default_fetch_interval_minutes: int = 5
    max_concurrent_feeds: int = 100
    fetch_timeout_seconds: int = 30
    max_articles_per_feed: int = 100

    # Quality
    min_article_length: int = 100
    enable_content_quality_check: bool = True
    enable_duplicate_url_check: bool = True

    def __post_init__(self):
        """Aplicar configuración desde variables de entorno."""
        self.auto_deduplication_enabled = (
            os.getenv("AUTO_DEDUPLICATION_ENABLED", "true").lower() == "true"
        )
        self.deduplication_batch_size = int(os.getenv("DEDUPLICATION_BATCH_SIZE", "50"))
        self.deduplication_similarity_threshold = float(
            os.getenv("DEDUPLICATION_SIMILARITY_THRESHOLD", "0.98")
        )
        self.default_fetch_interval_minutes = int(
            os.getenv("RSS_FETCH_INTERVAL_MINUTES", "15")
        )
        self.max_concurrent_feeds = int(os.getenv("RSS_MAX_CONCURRENT_FEEDS", "5"))
        self.fetch_timeout_seconds = int(os.getenv("RSS_FETCH_TIMEOUT_SECONDS", "30"))
        self.max_articles_per_feed = int(os.getenv("RSS_MAX_ARTICLES_PER_FEED", "100"))
        self.min_article_length = int(os.getenv("RSS_MIN_ARTICLE_LENGTH", "100"))
        self.enable_content_quality_check = (
            os.getenv("RSS_ENABLE_QUALITY_CHECK", "true").lower() == "true"
        )
        self.enable_duplicate_url_check = (
            os.getenv("RSS_ENABLE_URL_DUPLICATE_CHECK", "true").lower() == "true"
        )

    @classmethod
    def from_env(cls) -> "RssConfig":
        """Factory method para crear desde variables de entorno."""
        return cls()

    @property
    def is_deduplication_aggressive(self) -> bool:
        return self.deduplication_similarity_threshold < 0.9

    @property
    def is_high_frequency_fetch(self) -> bool:
        return self.default_fetch_interval_minutes < 10
