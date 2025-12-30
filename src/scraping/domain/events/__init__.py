"""Domain Events del bounded context de Scraping."""

from .completed import ScrapingCompleted
from .configuration_updated import ScrapingConfigurationUpdated
from .failed import ScrapingFailed
from .scraping_pipeline_completed import ScrapingPipelineCompleted
from .source_scraped import SourceScraped
from .started import ScrapingStarted

__all__ = [
    "ScrapingStarted",
    "ScrapingCompleted",
    "ScrapingFailed",
    "SourceScraped",
    "ScrapingConfigurationUpdated",
    "ScrapingPipelineCompleted",
]
